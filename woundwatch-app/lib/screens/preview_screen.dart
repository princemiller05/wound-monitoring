// After the camera captures a photo we land here to review it and add context
// before saving: a pain level (0–10), any symptoms, and an optional note. That
// extra info is what makes the data useful to a clinician later — a photo on its
// own doesn't tell you how the patient actually feels.
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/wound_photo.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';

class PreviewScreen extends StatefulWidget {
  final File imageFile;
  final DateTime timestamp;
  final int dayNumber;

  const PreviewScreen({
    super.key,
    required this.imageFile,
    required this.timestamp,
    required this.dayNumber,
  });

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  double _pain = 0;
  final Set<String> _symptoms = {};
  final _notes = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _notes.dispose();
    super.dispose();
  }

  Future<void> _upload() async {
    setState(() => _saving = true);
    final auth = context.read<AuthProvider>();
    final photos = context.read<PhotosProvider>();
    final patientId = auth.patient?.uid ?? 'local';

    final photo = WoundPhoto(
      id: 'ph-${DateTime.now().millisecondsSinceEpoch}',
      patientId: patientId,
      localPath: widget.imageFile.path,
      timestamp: widget.timestamp,
      dayNumber: widget.dayNumber,
      painLevel: _pain.round(),
      symptoms: _symptoms.toList(),
      notes: _notes.text.trim(),
    );

    // PHASE 1: saved in memory. PHASE 3: compress + upload to Azure here.
    photos.addPhoto(photo);
    await Future.delayed(const Duration(milliseconds: 400));

    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Photo saved')),
    );
    Navigator.of(context).pop(); // back to home
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Review & Notes')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(AppSizes.cardRadius),
                child: Image.file(
                  widget.imageFile,
                  width: double.infinity,
                  height: 260,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text('Day ${widget.dayNumber}',
                        style: const TextStyle(
                            color: AppColors.primary,
                            fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    DateFormat('d MMM yyyy, h:mm a').format(widget.timestamp),
                    style: const TextStyle(color: AppColors.textMuted),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              const Text('Pain level',
                  style:
                      TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Row(
                children: [
                  Expanded(
                    child: Slider(
                      value: _pain,
                      min: 0,
                      max: 10,
                      divisions: 10,
                      activeColor: AppColors.primary,
                      label: _pain.round().toString(),
                      onChanged: (v) => setState(() => _pain = v),
                    ),
                  ),
                  SizedBox(
                    width: 36,
                    child: Text('${_pain.round()}',
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              const Text('Symptoms',
                  style:
                      TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: kSymptoms.map((s) {
                  final selected = _symptoms.contains(s);
                  return FilterChip(
                    label: Text(s),
                    selected: selected,
                    selectedColor: AppColors.primaryLight,
                    checkmarkColor: AppColors.primary,
                    onSelected: (on) => setState(() {
                      // "None" is mutually exclusive with the real symptoms:
                      // picking it clears the rest, and picking any real
                      // symptom clears "None". Otherwise you'd get nonsense like
                      // "None + Redness".
                      if (s == 'None') {
                        _symptoms
                          ..clear()
                          ..add('None');
                      } else {
                        _symptoms.remove('None');
                        on ? _symptoms.add(s) : _symptoms.remove(s);
                      }
                    }),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),

              const Text('Notes (optional)',
                  style:
                      TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              TextField(
                controller: _notes,
                maxLength: 200,
                maxLines: 3,
                decoration: const InputDecoration(
                  hintText: 'How are you feeling?',
                ),
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed:
                          _saving ? null : () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(54),
                        side: const BorderSide(color: AppColors.primary),
                        foregroundColor: AppColors.primary,
                      ),
                      child: const Text('Retake'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _saving ? null : _upload,
                      child: _saving
                          ? const SizedBox(
                              height: 22,
                              width: 22,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Save'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
