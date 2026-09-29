/// A single wound photo plus the notes captured with it.
///
/// `localPath` points to the file on the phone. Later, when Azure upload is
/// added, we'll also store a `blobPath` for the cloud copy.
class WoundPhoto {
  final String id;
  final String patientId;
  final String localPath;
  final DateTime timestamp;
  final int dayNumber;
  final int painLevel; // 0–10
  final List<String> symptoms;
  final String notes;

  /// Where on the body this wound is. Captured per-photo at upload time (not at
  /// registration) — a general wound monitor doesn't assume one fixed site.
  final String? woundLocation;

  WoundPhoto({
    required this.id,
    required this.patientId,
    required this.localPath,
    required this.timestamp,
    required this.dayNumber,
    this.painLevel = 0,
    this.symptoms = const [],
    this.notes = '',
    this.woundLocation,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'patientId': patientId,
        'localPath': localPath,
        'timestamp': timestamp.toIso8601String(),
        'dayNumber': dayNumber,
        'painLevel': painLevel,
        'symptoms': symptoms,
        'notes': notes,
        'woundLocation': woundLocation,
      };

  factory WoundPhoto.fromMap(Map<String, dynamic> map) => WoundPhoto(
        id: map['id'] as String,
        patientId: map['patientId'] as String,
        localPath: map['localPath'] as String,
        timestamp: DateTime.parse(map['timestamp'] as String),
        dayNumber: map['dayNumber'] as int? ?? 0,
        painLevel: map['painLevel'] as int? ?? 0,
        symptoms: (map['symptoms'] as List?)?.cast<String>() ?? const [],
        notes: map['notes'] as String? ?? '',
        woundLocation: map['woundLocation'] as String?,
      );
}
