import 'package:flutter/material.dart';

/// App-wide constants: colors, sizing, and the symptom list.
///
/// Keeping these in one place means changing the brand color or spacing
/// only happens here, not scattered across every screen.
class AppColors {
  AppColors._();

  /// Primary accent (a deep clinical teal). Used sparingly — one accent only.
  static const Color primary = Color(0xFF0E7361);
  static const Color primaryDark = Color(0xFF0A574A);
  static const Color primaryLight = Color(0xFFE7F1EE); // tint for chips/fills

  // Cool, near-white clinical surfaces defined by hairline borders, not shadows.
  static const Color background = Color(0xFFF4F6F7);
  static const Color card = Colors.white;
  static const Color border = Color(0xFFE2E8E7);
  static const Color divider = Color(0xFFEDF1F0);

  // Ink hierarchy: strong heading ink, muted body, faint labels.
  static const Color textDark = Color(0xFF13201D);
  static const Color textMuted = Color(0xFF5F6E69);
  static const Color textFaint = Color(0xFF93A29D);

  // Healing-status colors (deeper, less neon — reads as medical, not playful).
  static const Color healingGood = Color(0xFF11816A);
  static const Color healingWatch = Color(0xFFB4830B);
  static const Color healingBad = Color(0xFFC0483F);

  // Tissue colors (used in the tissue chart).
  static const Color granulation = Color(0xFF2C9576);
  static const Color slough = Color(0xFFCF9A14);
  static const Color necrosis = Color(0xFF6E322E);
}

class AppSizes {
  AppSizes._();

  static const double screenPadding = 20.0;
  static const double cardRadius = 14.0;
  static const double cardPadding = 18.0;
  static const double gap = 14.0;
}

/// Symptom chips shown on the preview screen.
const List<String> kSymptoms = [
  'Redness',
  'Swelling',
  'Fever',
  'Discharge',
  'Odor',
  'None',
];

/// Wound-location options, chosen per-photo at upload time. A general wound
/// monitor covers wounds anywhere on the body, not just the foot.
const List<String> kWoundLocations = [
  'Foot',
  'Ankle',
  'Lower leg / shin',
  'Knee',
  'Thigh',
  'Hip / buttock',
  'Lower back',
  'Abdomen',
  'Chest',
  'Arm',
  'Hand',
  'Head / face',
  'Other',
];

/// Gender options for sign-up.
const List<String> kGenders = ['Male', 'Female', 'Prefer not to say'];
