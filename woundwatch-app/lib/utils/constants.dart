import 'package:flutter/material.dart';

/// App-wide constants: colors, sizing, and the symptom list.
///
/// Keeping these in one place means changing the brand color or spacing
/// only happens here, not scattered across every screen.
class AppColors {
  AppColors._();

  /// Primary accent (a calm, slightly deep clinical teal). Used sparingly.
  static const Color primary = Color(0xFF11816A);
  static const Color primaryDark = Color(0xFF0C6151);
  static const Color primaryLight = Color(0xFFEAF3F0); // tint for chips/fills

  // Cool, near-white clinical surfaces defined by hairline borders, not shadows.
  static const Color background = Color(0xFFF6F8F8);
  static const Color card = Colors.white;
  static const Color border = Color(0xFFE4EAE8);
  static const Color divider = Color(0xFFEDF1F0);

  // Ink hierarchy: strong heading ink, muted body, faint labels.
  static const Color textDark = Color(0xFF17211F);
  static const Color textMuted = Color(0xFF64726D);
  static const Color textFaint = Color(0xFF98A6A1);

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

  static const double screenPadding = 22.0;
  static const double cardRadius = 12.0;
  static const double gap = 16.0;
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

/// Wound-location options for the profile.
const List<String> kWoundLocations = [
  'Left foot',
  'Right foot',
  'Left toe',
  'Right toe',
  'Heel',
  'Other',
];

/// Diabetes-type options for the profile.
const List<String> kDiabetesTypes = ['Type 1', 'Type 2', 'Other'];

/// Gender options for sign-up.
const List<String> kGenders = ['Male', 'Female', 'Prefer not to say'];
