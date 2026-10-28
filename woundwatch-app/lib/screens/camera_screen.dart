import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:sensors_plus/sensors_plus.dart';
import '../providers/photos_provider.dart';
import '../services/image_quality.dart';
import '../utils/constants.dart';
import 'preview_screen.dart';

/// Capture screen. Uses image_picker, which opens the phone's real camera
/// (or gallery). Simpler and more reliable than a custom viewfinder; we can
/// upgrade to a live preview with the `camera` package later.
class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final _picker = ImagePicker();
  bool _busy = false;

  // Hold-steady: smoothed linear-acceleration magnitude (0 when still).
  StreamSubscription? _accelSub;
  Timer? _sensorFallback;
  bool _gotSensor = false;
  double _motion = 0;
  bool _steady = false;
  static const double _steadyThreshold = 0.45; // m/s^2 of movement

  @override
  void initState() {
    super.initState();
    try {
      _accelSub = userAccelerometerEventStream().listen((e) {
        _gotSensor = true;
        final mag = sqrt(e.x * e.x + e.y * e.y + e.z * e.z);
        _motion = _motion * 0.8 + mag * 0.2; // low-pass smoothing
        final steadyNow = _motion < _steadyThreshold;
        if (steadyNow != _steady && mounted) {
          setState(() => _steady = steadyNow);
        }
      }, onError: (_) => _enableWithoutSensor());
    } catch (_) {
      _enableWithoutSensor();
    }
    // If no sensor data arrives (emulator / no sensor), don't block capture.
    _sensorFallback = Timer(const Duration(seconds: 2), () {
      if (!_gotSensor) _enableWithoutSensor();
    });
  }

  void _enableWithoutSensor() {
    if (mounted && !_steady) setState(() => _steady = true);
  }

  @override
  void dispose() {
    _accelSub?.cancel();
    _sensorFallback?.cancel();
    super.dispose();
  }

  Future<void> _capture(ImageSource source) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1080,
        maxHeight: 1080,
      );
      if (file == null) {
        setState(() => _busy = false);
        return;
      }

      // On-device quality gate: reject blurry / badly-lit photos before saving.
      final quality = await ImageQuality.check(File(file.path));
      if (!mounted) return;
      if (!quality.ok) {
        setState(() => _busy = false);
        await _showRetake(quality.reason!);
        return;
      }

      // Duplicate check: is this essentially the same as the last photo?
      final photos = context.read<PhotosProvider>();
      final last = photos.lastCaptureHash;
      if (last != null &&
          ImageQuality.hamming(quality.hash, last) <=
              ImageQuality.duplicateMaxHamming) {
        setState(() => _busy = false);
        await _showRetake(
            'This looks like the same photo as last time. Take a fresh '
            'photo of the wound so the trend stays accurate.');
        return;
      }
      photos.lastCaptureHash = quality.hash;

      final dayNumber = photos.nextDayNumber();
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => PreviewScreen(
            imageFile: File(file.path),
            timestamp: DateTime.now(),
            dayNumber: dayNumber,
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        setState(() => _busy = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not open camera: $e')),
        );
      }
    }
  }

  Future<void> _showRetake(String reason) async {
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        icon: const Icon(Icons.image_not_supported_outlined,
            color: AppColors.healingWatch, size: 32),
        title: const Text("Let's retake that"),
        content: Text(reason),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK, retake'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Capture Wound Photo')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(28),
                decoration: const BoxDecoration(
                  color: AppColors.primaryLight,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.camera_alt,
                    size: 72, color: AppColors.primary),
              ),
              const SizedBox(height: 24),
              const Text(
                'Hold steady and fill the frame',
                style:
                    TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Good lighting and a clear, close shot of the wound give the '
                'best results.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textMuted),
              ),
              const SizedBox(height: 28),
              _SteadyIndicator(steady: _steady),
              const SizedBox(height: 14),
              ElevatedButton.icon(
                onPressed:
                    (_busy || !_steady) ? null : () => _capture(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: Text(_steady ? 'Open Camera' : 'Hold steady…'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _busy ? null : () => _capture(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Choose from Gallery'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(54),
                  side: const BorderSide(color: AppColors.primary),
                  foregroundColor: AppColors.primary,
                ),
              ),
              if (_busy) ...[
                const SizedBox(height: 24),
                const CircularProgressIndicator(),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Live hold-steady chip: green when the phone is still, amber while it moves.
class _SteadyIndicator extends StatelessWidget {
  final bool steady;
  const _SteadyIndicator({required this.steady});

  @override
  Widget build(BuildContext context) {
    final color = steady ? AppColors.healingGood : AppColors.healingWatch;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(steady ? Icons.check_circle : Icons.vibration,
              size: 18, color: color),
          const SizedBox(width: 8),
          Text(steady ? 'Steady — ready to shoot' : 'Hold the phone steady…',
              style: TextStyle(color: color, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
