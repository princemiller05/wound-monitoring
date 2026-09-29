import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;
import '../models/patient.dart';
import '../services/profile_service.dart';
import '../services/api_config.dart';

/// Holds the signed-in patient and auth actions.
///
/// #1 — now backed by real Firebase Auth: registration creates a real account,
/// a wrong password is rejected, and the patient id is the stable Firebase UID
/// (which also settles the ID-format question, #43).
class AuthProvider extends ChangeNotifier {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  Patient? _patient;

  Patient? get patient => _patient;
  bool get isLoggedIn => _patient != null;

  AuthProvider() {
    // Restore the session on launch if the user is already signed in.
    final u = _auth.currentUser;
    if (u != null) {
      _patient = Patient(
        uid: u.uid,
        fullName: u.displayName ?? (u.email?.split('@').first ?? 'Patient'),
        email: u.email ?? '',
      );
      _loadProfile(); // fill in the saved profile in the background
    }
  }

  /// Register a real account (#1).
  Future<void> signUp({
    required String fullName,
    required String email,
    required String password,
    DateTime? dateOfBirth,
    String? gender,
  }) async {
    try {
      final cred = await _auth.createUserWithEmailAndPassword(
          email: email.trim(), password: password);
      await cred.user?.updateDisplayName(fullName);
      _patient = Patient(
        uid: cred.user!.uid, // #43 — the Firebase UID is the patient id
        fullName: fullName,
        email: email.trim(),
        dateOfBirth: dateOfBirth,
        gender: gender,
      );
      notifyListeners();
    } on FirebaseAuthException catch (e) {
      throw Exception(_friendlyError(e));
    }
  }

  /// Real sign-in — a wrong password now actually fails (#1).
  Future<void> login({
    required String email,
    required String password,
  }) async {
    try {
      final cred = await _auth.signInWithEmailAndPassword(
          email: email.trim(), password: password);
      final u = cred.user!;
      _patient = Patient(
        uid: u.uid,
        fullName: u.displayName ?? email.split('@').first,
        email: u.email ?? email.trim(),
      );
      notifyListeners();
      await _loadProfile(); // pull the saved profile from the backend
    } on FirebaseAuthException catch (e) {
      throw Exception(_friendlyError(e));
    }
  }

  /// Turn Firebase error codes into messages a patient understands.
  String _friendlyError(FirebaseAuthException e) {
    switch (e.code) {
      case 'invalid-credential':
      case 'wrong-password':
      case 'user-not-found':
        return 'Incorrect email or password.';
      case 'email-already-in-use':
        return 'An account with this email already exists.';
      case 'weak-password':
        return 'Password is too weak (use at least 6 characters).';
      case 'invalid-email':
        return 'That email address is not valid.';
      case 'network-request-failed':
        return 'No internet connection.';
      default:
        return e.message ?? 'Authentication failed.';
    }
  }

  /// Load this patient's saved profile from the backend (persists across
  /// logins and reinstalls). Best-effort — a missing profile is fine.
  Future<void> _loadProfile() async {
    final p = _patient;
    if (p == null || !ApiConfig.useRealBackend) return;
    try {
      final resp = await http.get(
        ApiConfig.url('get_patient_history', {'patient_id': p.uid}),
      );
      if (resp.statusCode != 200) return;
      final data = jsonDecode(resp.body) as Map<String, dynamic>;
      final view = data['patient'] as Map<String, dynamic>?;
      if (view == null) return;
      p.fullName = (view['full_name'] as String?)?.isNotEmpty == true
          ? view['full_name'] as String
          : p.fullName;
      p.gender = view['sex'] as String?;
      p.phone = view['phone'] as String?;
      p.heightCm = (view['height_cm'] as num?)?.toDouble();
      p.weightKg = (view['weight_kg'] as num?)?.toDouble();
      p.doctorEmails =
          (view['doctor_emails'] as List?)?.cast<String>() ?? p.doctorEmails;
      notifyListeners();
    } catch (_) {
      // ignore — profile just stays as-is
    }
  }

  /// Save the general health profile (phone, height, weight).
  Future<void> completeProfile({
    String? phone,
    double? heightCm,
    double? weightKg,
  }) async {
    final p = _patient;
    if (p == null) return;
    p.phone = phone;
    p.heightCm = heightCm;
    p.weightKg = weightKg;
    notifyListeners();
    await ProfileService.save(p); // #13 persist to Firestore
  }

  /// Update an existing profile (edit screen) — also saves to Firestore.
  Future<void> updateProfile(Patient updated) async {
    _patient = updated;
    notifyListeners();
    await ProfileService.save(updated); // #13
  }

  /// Add a doctor by email (a patient can have several). Saves to Firestore.
  Future<void> addDoctor(String email) async {
    final p = _patient;
    if (p == null) return;
    final e = email.trim().toLowerCase();
    if (e.isEmpty || p.doctorEmails.contains(e)) return;
    p.doctorEmails.add(e);
    notifyListeners();
    await ProfileService.save(p);
  }

  Future<void> removeDoctor(String email) async {
    final p = _patient;
    if (p == null) return;
    p.doctorEmails.remove(email);
    notifyListeners();
    await ProfileService.save(p);
  }

  Future<void> signOut() async {
    await _auth.signOut();
    _patient = null;
    notifyListeners();
  }
}
