/// A patient's profile. In this phase it lives in memory; later it will be
/// stored in Firestore under the `patients` collection.
class Patient {
  final String uid;
  String fullName;
  String email;
  DateTime? dateOfBirth;
  String? gender;

  // General health profile — applies to any patient with any wound.
  String? phone;
  double? heightCm;
  double? weightKg;

  /// The patient's doctors, by email. A patient may see more than one doctor,
  /// so this is a list managed from the home screen (not asked at signup).
  List<String> doctorEmails;

  Patient({
    required this.uid,
    required this.fullName,
    required this.email,
    this.dateOfBirth,
    this.gender,
    this.phone,
    this.heightCm,
    this.weightKg,
    List<String>? doctorEmails,
  }) : doctorEmails = doctorEmails ?? [];

  /// #8 — BMI computed from height and weight (kg / m²), or null if unknown.
  double? get bmi {
    final h = heightCm, w = weightKg;
    if (h != null && w != null && h > 0) {
      final m = h / 100.0;
      return double.parse((w / (m * m)).toStringAsFixed(1));
    }
    return null;
  }

  /// The JSON payload sent to the save_profile function (#13).
  /// General person-level fields only — wound details belong to each photo.
  Map<String, dynamic> toProfilePayload() => {
        'patient_id': uid,
        'full_name': fullName,
        'phone': phone,
        'dob': dateOfBirth?.toIso8601String(),
        'sex': gender,
        'height_cm': heightCm,
        'weight_kg': weightKg,
        'doctor_emails': doctorEmails,
      };
}
