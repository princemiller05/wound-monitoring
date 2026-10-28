import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:image/image.dart' as img;

/// Result of the on-device photo quality check done at capture time.
class QualityResult {
  final bool ok;
  final String? reason;   // null when ok; else a retake message for the patient
  final double sharpness; // Laplacian variance (higher = sharper)
  final double brightness; // mean luminance 0..255
  final String hash;      // 64-char perceptual dHash (for duplicate detection)

  const QualityResult(this.ok, this.reason, this.sharpness, this.brightness,
      [this.hash = '']);
}

/// Fast, fully on-device quality gate: rejects blurry or badly-lit wound photos
/// BEFORE they're saved/uploaded, and tells the patient to retake.
///
/// - Blur: variance of the Laplacian. A sharp photo has strong edges (high
///   variance); a blurry one has few (low variance).
/// - Lighting: mean brightness (too dark / washed-out) plus a glare check
///   (too many pure-white pixels).
///
/// Thresholds are deliberately forgiving and tunable — a real deployment would
/// calibrate them on sample photos from the target phones.
class ImageQuality {
  // Tune these on real device photos if needed.
  static const double minSharpness = 90.0;   // below -> blurry
  static const double minBrightness = 45.0;  // below -> too dark
  static const double maxBrightness = 220.0; // above -> washed out
  static const double maxGlareFraction = 0.35; // >35% near-white -> glare
  static const double minContrastStd = 10.0; // below -> flat/empty frame
  static const int minResolution = 300;      // px, shortest side
  static const int duplicateMaxHamming = 6;  // <= -> same as last photo

  /// Hamming distance between two dHash strings (number of differing bits).
  static int hamming(String a, String b) {
    if (a.isEmpty || b.isEmpty || a.length != b.length) return 64;
    var d = 0;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) d++;
    }
    return d;
  }

  /// Analyse [file] off the UI thread. Never throws — returns ok on any error
  /// so a quirky image can't block the patient entirely.
  static Future<QualityResult> check(File file) async {
    try {
      final bytes = await file.readAsBytes();
      final r = await compute(_analyze, bytes);
      debugPrint('[quality] sharpness=${r.sharpness.toStringAsFixed(1)} '
          'brightness=${r.brightness.toStringAsFixed(1)} '
          'ok=${r.ok}${r.ok ? '' : ' (${r.reason})'}');
      return r;
    } catch (_) {
      return const QualityResult(true, null, 0, 0);
    }
  }
}

/// Runs in a background isolate (pure function, top-level for `compute`).
String _dhash(img.Image decoded) {
  // 9x8 grayscale; compare each pixel to its right neighbour -> 64 bits.
  final small = img.grayscale(img.copyResize(decoded, width: 9, height: 8));
  final sb = StringBuffer();
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 8; x++) {
      final l = small.getPixel(x, y).r;
      final r = small.getPixel(x + 1, y).r;
      sb.write(l < r ? '1' : '0');
    }
  }
  return sb.toString();
}

QualityResult _analyze(Uint8List bytes) {
  final decoded = img.decodeImage(bytes);
  if (decoded == null) return const QualityResult(true, null, 0, 0);

  final hash = _dhash(decoded);

  // Too low resolution to analyse reliably.
  if (decoded.width < ImageQuality.minResolution ||
      decoded.height < ImageQuality.minResolution) {
    return QualityResult(false,
        "This image is too small — take a clearer, closer photo.",
        0, 0, hash);
  }

  // Downscale for speed — quality metrics don't need full resolution.
  final resized = decoded.width > 512
      ? img.copyResize(decoded, width: 512)
      : decoded;
  final gray = img.grayscale(resized);
  final w = gray.width, h = gray.height;

  // Read luminance into a flat array once.
  final lum = Float64List(w * h);
  double sum = 0, sumSq = 0;
  int nearWhite = 0;
  for (int y = 0; y < h; y++) {
    for (int x = 0; x < w; x++) {
      final v = gray.getPixel(x, y).r.toDouble(); // grayscale: r==g==b
      lum[y * w + x] = v;
      sum += v;
      sumSq += v * v;
      if (v >= 250) nearWhite++;
    }
  }
  final n = w * h;
  final brightness = sum / n;
  final glare = nearWhite / n;
  final contrastStd = math.sqrt(math.max(0, sumSq / n - brightness * brightness));

  // Laplacian variance over the interior.
  double lSum = 0, lSumSq = 0;
  int cnt = 0;
  for (int y = 1; y < h - 1; y++) {
    for (int x = 1; x < w - 1; x++) {
      final i = y * w + x;
      final lap = 4 * lum[i] - lum[i - 1] - lum[i + 1] - lum[i - w] - lum[i + w];
      lSum += lap;
      lSumSq += lap * lap;
      cnt++;
    }
  }
  final mean = cnt > 0 ? lSum / cnt : 0;
  final sharpness = cnt > 0 ? (lSumSq / cnt) - (mean * mean) : 0.0;

  // Decide — lighting first (blur metric is unreliable in bad light).
  if (brightness < ImageQuality.minBrightness) {
    return QualityResult(false,
        "It's too dark — move to brighter, even light and retake.",
        sharpness, brightness, hash);
  }
  if (brightness > ImageQuality.maxBrightness ||
      glare > ImageQuality.maxGlareFraction) {
    return QualityResult(false,
        "Too much glare — avoid direct flash or sunlight and retake.",
        sharpness, brightness, hash);
  }
  if (contrastStd < ImageQuality.minContrastStd) {
    return QualityResult(false,
        "Point the camera at the wound — this photo looks blank or uniform.",
        sharpness, brightness, hash);
  }
  if (sharpness < ImageQuality.minSharpness) {
    return QualityResult(false,
        "The photo looks blurry — hold steady, tap the wound to focus, "
        "then retake.",
        sharpness, brightness, hash);
  }
  return QualityResult(true, null, sharpness, brightness, hash);
}
