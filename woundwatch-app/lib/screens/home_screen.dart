import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';
import '../theme/app_theme.dart';
import 'camera_screen.dart';
import 'import_photos_screen.dart';
import 'doctors_screen.dart';

class HomeScreen extends StatelessWidget {
  /// Lets the dashboard switch the bottom-nav tab (e.g. tap healing card → Progress).
  final void Function(int tabIndex) onNavigateToTab;

  const HomeScreen({super.key, required this.onNavigateToTab});

  @override
  Widget build(BuildContext context) {
    final patient = context.watch<AuthProvider>().patient;
    final photos = context.watch<PhotosProvider>();
    final firstName = (patient?.fullName ?? 'there').split(' ').first;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(AppSizes.screenPadding, 8,
              AppSizes.screenPadding, AppSizes.screenPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Greeting: date overline + name. Sparse, no filler.
              Text(DateFormat('EEEE, d MMMM').format(DateTime.now()).toUpperCase(),
                  style: AppText.overline),
              const SizedBox(height: 6),
              Text(firstName, style: AppText.h1),
              const SizedBox(height: 22),

              // Overview — the healing readout, presented as real data.
              const Text('OVERVIEW', style: AppText.overline),
              const SizedBox(height: 10),
              _HealingCard(photos: photos, onTap: () => onNavigateToTab(2)),
              const SizedBox(height: 22),

              // Primary action.
              const Text('TRACK', style: AppText.overline),
              const SizedBox(height: 10),
              _CaptureButton(
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const CameraScreen()),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: _SecondaryAction(
                      icon: Icons.collections_outlined,
                      label: 'Import photos',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                            builder: (_) => const ImportPhotosScreen()),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _SecondaryAction(
                      icon: Icons.medical_services_outlined,
                      label: 'My doctors',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const DoctorsScreen()),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Recent photos.
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('RECENT', style: AppText.overline),
                  TextButton(
                    onPressed: () => onNavigateToTab(1),
                    style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: const Size(0, 0),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap),
                    child: const Text('See all'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _RecentPhotosRow(photos: photos.photosNewestFirst),
            ],
          ),
        ),
      ),
    );
  }
}

/// Primary capture action — a single solid accent row. Restrained copy, a plain
/// icon (no decorative tinted box), one clear affordance.
class _CaptureButton extends StatelessWidget {
  final VoidCallback onTap;
  const _CaptureButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.primary,
      borderRadius: BorderRadius.circular(AppSizes.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSizes.cardRadius),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
          child: Row(
            children: [
              const Icon(Icons.camera_alt_outlined,
                  color: Colors.white, size: 22),
              const SizedBox(width: 14),
              const Expanded(
                child: Text('New wound photo',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 15.5,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.1)),
              ),
              Icon(Icons.arrow_forward,
                  color: Colors.white.withValues(alpha: 0.85), size: 19),
            ],
          ),
        ),
      ),
    );
  }
}

/// Understated secondary action — hairline-bordered tile, icon over label.
class _SecondaryAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _SecondaryAction(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(AppSizes.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSizes.cardRadius),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppSizes.cardRadius),
            border: Border.all(color: AppColors.border),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
          child: Row(
            children: [
              Icon(icon, size: 19, color: AppColors.primary),
              const SizedBox(width: 10),
              Expanded(
                child: Text(label,
                    style: const TextStyle(
                        fontSize: 13.5,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textDark)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// The healing readout, built like a clinical stat: a big number with its unit
/// and label, plus a small trend indicator — not a chatty "looking positive".
class _HealingCard extends StatelessWidget {
  final PhotosProvider photos;
  final VoidCallback onTap;
  const _HealingCard({required this.photos, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final pred = photos.prediction;
    final hasData = pred != null && pred.enoughVisits;
    final pct = hasData ? (pred.healingProbability * 100).round() : null;
    String _labelText(String s) => s.isEmpty
        ? 'Tracking'
        : s[0].toUpperCase() + s.substring(1);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSizes.cardRadius),
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.cardPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Healing likelihood',
                      style: TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textMuted)),
                  const Icon(Icons.chevron_right,
                      color: AppColors.textFaint, size: 20),
                ],
              ),
              const SizedBox(height: 14),
              if (hasData) ...[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text('$pct', style: AppText.stat),
                    const SizedBox(width: 2),
                    const Padding(
                      padding: EdgeInsets.only(bottom: 4),
                      child: Text('%',
                          style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textFaint)),
                    ),
                    const Spacer(),
                    _TrendPill(label: _labelText(pred.predictedLabel)),
                  ],
                ),
                const SizedBox(height: 10),
                _MiniBar(value: pred.healingProbability),
              ] else ...[
                const SizedBox(height: 2),
                Text(
                  pred == null
                      ? 'Take your first photo to begin tracking.'
                      : 'One more visit needed to estimate healing.',
                  style: AppText.muted,
                ),
                const SizedBox(height: 4),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// A slim progress rail under the stat — reads as a measurement, not decoration.
class _MiniBar extends StatelessWidget {
  final double value; // 0..1
  const _MiniBar({required this.value});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(3),
      child: LinearProgressIndicator(
        value: value.clamp(0.0, 1.0),
        minHeight: 5,
        backgroundColor: AppColors.primaryLight,
        valueColor: const AlwaysStoppedAnimation(AppColors.primary),
      ),
    );
  }
}

class _TrendPill extends StatelessWidget {
  final String label;
  const _TrendPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primaryLight,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AppColors.primaryDark)),
    );
  }
}

class _RecentPhotosRow extends StatelessWidget {
  final List photos;
  const _RecentPhotosRow({required this.photos});

  @override
  Widget build(BuildContext context) {
    if (photos.isEmpty) {
      return Container(
        height: 96,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(AppSizes.cardRadius),
          border: Border.all(color: AppColors.border),
        ),
        child: const Text('No photos yet',
            style: TextStyle(color: AppColors.textMuted, fontSize: 13.5)),
      );
    }

    return SizedBox(
      height: 150,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: photos.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (_, i) {
          final p = photos[i];
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Image.file(
                  File(p.localPath),
                  width: 100,
                  height: 100,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 100,
                    height: 100,
                    color: AppColors.primaryLight,
                    child: const Icon(Icons.image_not_supported_outlined,
                        color: AppColors.primary),
                  ),
                ),
              ),
              const SizedBox(height: 7),
              Text('Day ${p.dayNumber}',
                  style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textDark)),
              Text(DateFormat('d MMM').format(p.timestamp),
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textFaint)),
            ],
          );
        },
      ),
    );
  }
}
