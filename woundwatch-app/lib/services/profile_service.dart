import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/patient.dart';
import 'api_config.dart';

/// #13 — persists the patient profile to Firestore via the save_profile
/// function. Varsha's dashboard reads this. No-op in mock mode.
class ProfileService {
  static Future<void> save(Patient p) async {
    if (!ApiConfig.useRealBackend) return;
    try {
      final resp = await http.post(
        ApiConfig.url('save_profile', const {}),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(p.toProfilePayload()),
      );
      if (resp.statusCode != 200) {
        debugPrint('[save_profile] failed ${resp.statusCode}: ${resp.body}');
      }
    } catch (e) {
      debugPrint('[save_profile] error $e');
    }
  }
}
