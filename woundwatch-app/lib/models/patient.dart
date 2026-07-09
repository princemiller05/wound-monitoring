/// A patient's profile. In this phase it lives in memory; later it will be
/// stored in Firestore under the `patients` collection.
class Patient {
  final String uid;
  String fullName;
  String email;
  DateTime? dateOfBirth;
  String? gender;

  // Medical profile (filled on the profile-setup screen).
  String? phone;
  String? clinicianName;
  String? clinicianEmail;
  String? woundLocation;
  DateTime? diagnosisDate;
  String? diabetesType;

  Patient({
    required this.uid,
    required this.fullName,
    required this.email,
    this.dateOfBirth,
    this.gender,
    this.phone,
    this.clinicianName,
    this.clinicianEmail,
    this.woundLocation,
    this.diagnosisDate,
    this.diabetesType,
  });

  /// True once the patient has completed the medical profile step.
  bool get profileComplete => woundLocation != null && diabetesType != null;

  Map<String, dynamic> toMap() => {
        'uid': uid,
        'fullName': fullName,
        'email': email,
        'dateOfBirth': dateOfBirth?.toIso8601String(),
        'gender': gender,
        'phone': phone,
        'clinicianName': clinicianName,
        'clinicianEmail': clinicianEmail,
        'woundLocation': woundLocation,
        'diagnosisDate': diagnosisDate?.toIso8601String(),
        'diabetesType': diabetesType,
      };

  factory Patient.fromMap(Map<String, dynamic> map) => Patient(
        uid: map['uid'] as String,
        fullName: map['fullName'] as String? ?? '',
        email: map['email'] as String? ?? '',
        dateOfBirth: map['dateOfBirth'] != null
            ? DateTime.tryParse(map['dateOfBirth'] as String)
            : null,
        gender: map['gender'] as String?,
        phone: map['phone'] as String?,
        clinicianName: map['clinicianName'] as String?,
        clinicianEmail: map['clinicianEmail'] as String?,
        woundLocation: map['woundLocation'] as String?,
        diagnosisDate: map['diagnosisDate'] != null
            ? DateTime.tryParse(map['diagnosisDate'] as String)
            : null,
        diabetesType: map['diabetesType'] as String?,
      );
}
