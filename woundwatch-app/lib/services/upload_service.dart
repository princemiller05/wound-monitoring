import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'api_config.dart';

/// Handles getting a wound photo up to Azure Blob Storage.
///
/// Flow (only runs when a real backend is configured):
///   1. Compress the photo (~500 KB instead of 5-10 MB).
///   2. Ask the `get_upload_url` function for a short-lived SAS upload URL.
///   3. HTTP PUT the bytes straight to Blob Storage.
///
/// The filename MUST be `{patientId}/{patientId}_DAY{n}.jpg` — the whole backend
/// keys off it (the blob trigger reads the patient id and day number from it).
class UploadService {
  /// Compress an image down to a sensible upload size (1080p, quality 85).
  static Future<File> _compress(File original) async {
    final dir = await getTemporaryDirectory();
    final target =
        '${dir.path}/ww_${DateTime.now().millisecondsSinceEpoch}.jpg';
    final result = await FlutterImageCompress.compressAndGetFile(
      original.absolute.path,
      target,
      quality: 85,
      minWidth: 1080,
      minHeight: 1080,
      format: CompressFormat.jpeg,
    );
    // If compression somehow fails, fall back to the original file.
    return result == null ? original : File(result.path);
  }

  /// Upload one photo. Returns the blob path on success, or throws.
  ///
  /// [patientId] e.g. "CASE_001", [dayNumber] e.g. 7.
  static Future<String> uploadPhoto({
    required File image,
    required String patientId,
    required int dayNumber,
  }) async {
    // Unique, honest filename: patient + real day number + capture timestamp.
    // The timestamp makes every photo its own record — nothing overwrites, and
    // multiple photos on the same day coexist with their true times.
    final ts = DateTime.now().millisecondsSinceEpoch;
    final filename = '${patientId}_DAY${dayNumber}_$ts.jpg';

    // 1) compress
    final compressed = await _compress(image);

    // 2) ask the backend for a secure, short-lived upload URL
    final infoResp = await http.get(ApiConfig.url(
      'get_upload_url',
      {'patient_id': patientId, 'filename': filename},
    ));
    if (infoResp.statusCode != 200) {
      throw Exception('Could not get upload URL (${infoResp.statusCode})');
    }
    final info = jsonDecode(infoResp.body) as Map<String, dynamic>;
    final uploadUrl = info['upload_url'] as String;
    final blobPath = info['blob_path'] as String;

    // 3) PUT the bytes to Blob Storage
    final bytes = await compressed.readAsBytes();
    final putResp = await http.put(
      Uri.parse(uploadUrl),
      headers: {
        'x-ms-blob-type': 'BlockBlob',
        'Content-Type': 'image/jpeg',
      },
      body: bytes,
    );
    if (putResp.statusCode < 200 || putResp.statusCode >= 300) {
      throw Exception('Blob upload failed (${putResp.statusCode})');
    }

    debugPrint('[upload] $blobPath uploaded (${bytes.length ~/ 1024} KB)');
    return blobPath;
  }
}
