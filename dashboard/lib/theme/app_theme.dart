import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const Color background = Color(0xFF0F1115);
  static const Color surface = Color(0xFF1E2022);
  static const Color glassBorder = Color(0x1AFFFFFF);
  static const Color accentGreen = Color(0xFF32D74B);
  static const Color accentYellow = Color(0xFFFFD60A);
  static const Color accentRed = Color(0xFFFF4D4D);
  static const Color textPrimary = Color(0xFFE2E2E5);
  static const Color textSecondary = Color(0xFFC6C6CB);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      primaryColor: accentGreen,
      textTheme: GoogleFonts.interTextTheme().apply(
        bodyColor: textPrimary,
        displayColor: textPrimary,
      ),
      cardTheme: CardTheme(
        color: surface.withOpacity(0.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: glassBorder, width: 1),
        ),
      ),
    );
  }

  static BoxDecoration glassDecoration({double blur = 20}) {
    return BoxDecoration(
      color: Colors.white.withOpacity(0.05),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: glassBorder),
    );
  }
}
