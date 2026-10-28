import 'dart:io';
import 'package:flutter/material.dart';
import '../utils/constants.dart';

/// Shows a wound photo from the local file when we have it (freshly captured
/// this session), otherwise from its cloud URL (loaded back from the backend so
/// photos survive reopening the app). Falls back to a placeholder on error.
class WoundImage extends StatelessWidget {
  final String localPath;
  final String? remoteUrl;
  final double? size; // square if set
  final double? width;
  final double? height;
  final BoxFit fit;

  const WoundImage({
    super.key,
    required this.localPath,
    required this.remoteUrl,
    this.size,
    this.width,
    this.height,
    this.fit = BoxFit.cover,
  });

  Widget _placeholder(double? w, double? h) => Container(
        width: w,
        height: h,
        color: AppColors.primaryLight,
        child: const Icon(Icons.image_not_supported_outlined,
            color: AppColors.primary),
      );

  @override
  Widget build(BuildContext context) {
    final w = width ?? size;
    final h = height ?? size;

    final hasLocal = localPath.isNotEmpty && File(localPath).existsSync();
    if (hasLocal) {
      return Image.file(File(localPath),
          width: w, height: h, fit: fit,
          errorBuilder: (_, __, ___) => _placeholder(w, h));
    }
    if (remoteUrl != null && remoteUrl!.isNotEmpty) {
      return Image.network(remoteUrl!,
          width: w, height: h, fit: fit,
          errorBuilder: (_, __, ___) => _placeholder(w, h),
          loadingBuilder: (ctx, child, progress) => progress == null
              ? child
              : Container(
                  width: w,
                  height: h,
                  color: AppColors.primaryLight,
                  child: const Center(
                    child: SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                ));
    }
    return _placeholder(w, h);
  }
}
