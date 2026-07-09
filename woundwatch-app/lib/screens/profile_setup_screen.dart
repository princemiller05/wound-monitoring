// Shown once, right after sign-up: the patient fills in their medical profile
// (clinician contact, wound location, diagnosis date, diabetes type). This is
// the context a clinician needs, and later it'll feed into the healing model.
// On save we drop the patient into the main app (home tab).
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import 'main_scaffold.dart';

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phone = TextEditingController();
  final _clinicianName = TextEditingController();
  final _clinicianEmail = TextEditingController();
  String? _woundLocation;
  String? _diabetesType;
  DateTime? _diagnosisDate;
  bool _loading = false;

  @override
  void dispose() {
    _phone.dispose();
    _clinicianName.dispose();
    _clinicianEmail.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(now.year - 10),
      lastDate: now,
    );
    if (picked != null) setState(() => _diagnosisDate = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    await context.read<AuthProvider>().completeProfile(
          phone: _phone.text.trim(),
          clinicianName: _clinicianName.text.trim(),
          clinicianEmail: _clinicianEmail.text.trim(),
          woundLocation: _woundLocation,
          diagnosisDate: _diagnosisDate,
          diabetesType: _diabetesType,
        );
    if (!mounted) return;
    setState(() => _loading = false);
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const MainScaffold()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Complete Your Profile')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'This helps your clinician follow your healing.',
                  style: TextStyle(color: AppColors.textMuted),
                ),
                const SizedBox(height: 20),
                TextFormField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(labelText: 'Phone number'),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Required' : null,
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _clinicianName,
                  decoration:
                      const InputDecoration(labelText: 'Clinician name'),
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _clinicianEmail,
                  keyboardType: TextInputType.emailAddress,
                  decoration:
                      const InputDecoration(labelText: 'Clinician email'),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: _woundLocation,
                  decoration:
                      const InputDecoration(labelText: 'Wound location'),
                  items: kWoundLocations
                      .map((g) =>
                          DropdownMenuItem(value: g, child: Text(g)))
                      .toList(),
                  onChanged: (v) => setState(() => _woundLocation = v),
                  validator: (v) => v == null ? 'Required' : null,
                ),
                const SizedBox(height: 14),
                InkWell(
                  onTap: _pickDate,
                  child: InputDecorator(
                    decoration:
                        const InputDecoration(labelText: 'Diagnosis date'),
                    child: Text(
                      _diagnosisDate == null
                          ? 'Select date'
                          : DateFormat('d MMM yyyy').format(_diagnosisDate!),
                      style: TextStyle(
                        color: _diagnosisDate == null
                            ? AppColors.textMuted
                            : AppColors.textDark,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: _diabetesType,
                  decoration:
                      const InputDecoration(labelText: 'Diabetes type'),
                  items: kDiabetesTypes
                      .map((g) =>
                          DropdownMenuItem(value: g, child: Text(g)))
                      .toList(),
                  onChanged: (v) => setState(() => _diabetesType = v),
                  validator: (v) => v == null ? 'Required' : null,
                ),
                const SizedBox(height: 28),
                ElevatedButton(
                  onPressed: _loading ? null : _submit,
                  child: _loading
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Save & Continue'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
