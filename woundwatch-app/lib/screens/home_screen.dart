import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';
import '../theme/app_theme.dart';
import 'camera_screen.dart';

class HomeScreen extends StatelessWidget {
  /// Lets the dashboard switch the bottom-nav tab (e.g. tap healing card → Progress).
  final void Function(int tabIndex) onNavigateToTab;

  const HomeScreen({super.key, required this.onNavigateToTab});

  @override
  Widget build(BuildContext context) {
    final patient = context.watch<AuthProvider>().patient;
    final photos = context.watch<PhotosProvider>();
    final firstName =
        (patient?.fullName ?? 'there').split(' ').first;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              Text('Good to see you,',
                  style: AppText.muted.copyWith(fontSize: 15)),
              const SizedBox(height: 2),
              Text(firstName, style: AppText.h1),
              const SizedBox(height: 26),

              // Primary action — a calm, full-width capture row (no glow).
              _CaptureButton(
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const CameraScreen()),
                ),
              ),
              const SizedBox(height: 28),

              const Text('OVERVIEW', style: AppText.overline),
              const SizedBox(height: 10),
              _HealingCard(
                photos: photos,
                onTap: () => onNavigateToTab(2),
              ),
              const SizedBox(height: 26),

              // Recent photos row.
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.center,
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
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }
}

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
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.camera_alt_outlined,
                    color: Colors.white, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Take a wound photo',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600)),
                    const SizedBox(height: 2),
                    Text('Capture today’s photo to track healing',
                        style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.85),
                            fontSize: 12.5)),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward,
                  color: Colors.white.withValues(alpha: 0.9), size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _HealingCard extends StatelessWidget {
  final PhotosProvider photos;
  final VoidCallback onTap;
  const _HealingCard({required this.photos, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final pred = photos.prediction;
    final hasData = pred != null;
    final pct = hasData ? (pred.healingProbability * 100).round() : null;

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSizes.cardRadius),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: const BoxDecoration(
                  color: AppColors.primaryLight,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.trending_up,
                    color: AppColors.primary, size: 32),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Healing Progress',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(
                      hasData
                          ? '$pct% — looking positive'
                          : 'Take your first photo to see progress',
                      style: const TextStyle(color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
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
        height: 120,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppSizes.cardRadius),
          border: Border.all(color: const Color(0xFFE2E8E5)),
        ),
        child: const Text('No photos yet',
            style: TextStyle(color: AppColors.textMuted)),
      );
    }

    return SizedBox(
      height: 164,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: photos.length,
        separatorBuilder: (_, __) => const SizedBox(width: 12),
        itemBuilder: (_, i) {
          final p = photos[i];
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(
                  File(p.localPath),
                  width: 96,
                  height: 96,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 96,
                    height: 96,
                    color: AppColors.primaryLight,
                    child: const Icon(Icons.image_not_supported,
                        color: AppColors.primary),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Text('Day ${p.dayNumber}',
                  style: const TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w600)),
              Text(DateFormat('d MMM').format(p.timestamp),
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textMuted)),
            ],
          );
        },
      ),
    );
  }
}
