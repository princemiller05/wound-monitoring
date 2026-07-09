import 'package:flutter/foundation.dart';
import '../models/patient.dart';

/// Holds the signed-in patient and basic auth actions.
///
/// PHASE 1 (now): everything is in memory and "auth" always succeeds — there's
/// no real password check. This lets us build and demo the full UI.
///
/// PHASE 2 (later): replace the bodies of signUp/login/signOut with Firebase
/// Auth calls, and load/save the profile from Firestore. The rest of the app
/// talks to this provider, so screens won't need to change.
class AuthProvider extends ChangeNotifier {
  Patient? _patient;

  Patient? get patient => _patient;
  bool get isLoggedIn => _patient != null;

  /// Mock sign-up: creates an in-memory patient. Always succeeds.
  Future<void> signUp({
    required String fullName,
    required String email,
    required String password,
    DateTime? dateOfBirth,
    String? gender,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600)); // fake network
    _patient = Patient(
      uid: 'local-${DateTime.now().millisecondsSinceEpoch}',
      fullName: fullName,
      email: email,
      dateOfBirth: dateOfBirth,
      gender: gender,
    );
    notifyListeners();
  }

  /// Mock login: accepts any email/password and creates a demo patient.
  Future<void> login({
    required String email,
    required String password,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600));
    _patient = Patient(
      uid: 'local-${email.hashCode}',
      fullName: email.split('@').first,
      email: email,
      woundLocation: 'Left foot', // pre-filled so demo login skips setup
      diabetesType: 'Type 2',
      diagnosisDate: DateTime.now().subtract(const Duration(days: 20)),
    );
    notifyListeners();
  }

  /// Save the medical profile collected on the setup screen.
  Future<void> completeProfile({
    String? phone,
    String? clinicianName,
    String? clinicianEmail,
    String? woundLocation,
    DateTime? diagnosisDate,
    String? diabetesType,
  }) async {
    final p = _patient;
    if (p == null) return;
    p.phone = phone;
    p.clinicianName = clinicianName;
    p.clinicianEmail = clinicianEmail;
    p.woundLocation = woundLocation;
    p.diagnosisDate = diagnosisDate;
    p.diabetesType = diabetesType;
    notifyListeners();
  }

  /// Update an existing profile (edit screen).
  Future<void> updateProfile(Patient updated) async {
    _patient = updated;
    notifyListeners();
  }

  void signOut() {
    _patient = null;
    notifyListeners();
  }
}
