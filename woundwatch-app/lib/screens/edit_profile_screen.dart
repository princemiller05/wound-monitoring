// Reached from the Profile tab. Pre-fills every field from the current patient,
// lets them change anything, and saves it back to AuthProvider. Also holds the
// log-out button (which clears the photo list too, so the next user starts
// clean).
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/patient.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';
import 'login_screen.dart';

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _name;
  late TextEditingController _phone;
  late TextEditingController _clinicianName;
  late TextEditingController _clinicianEmail;
  String? _woundLocation;
  String? _diabetesType;
  DateTime? _diagnosisDate;

  @override
  void initState() {
    super.initState();
    final p = context.read<AuthProvider>().patient!;
    _name = TextEditingController(text: p.fullName);
    _phone = TextEditingController(text: p.phone ?? '');
    _clinicianName = TextEditingController(text: p.clinicianName ?? '');
    _clinicianEmail = TextEditingController(text: p.clinicianEmail ?? '');
    _woundLocation = p.woundLocation;
    _diabetesType = p.diabetesType;
    _diagnosisDate = p.diagnosisDate;
  }

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _clinicianName.dispose();
    _clinicianEmail.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _diagnosisDate ?? now,
      firstDate: DateTime(now.year - 10),
      lastDate: now,
    );
    if (picked != null) setState(() => _diagnosisDate = picked);
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    final old = auth.patient!;
    final updated = Patient(
      uid: old.uid,
      fullName: _name.text.trim(),
      email: old.email,
      dateOfBirth: old.dateOfBirth,
      gender: old.gender,
      phone: _phone.text.trim(),
      clinicianName: _clinicianName.text.trim(),
      clinicianEmail: _clinicianEmail.text.trim(),
      woundLocation: _woundLocation,
      diagnosisDate: _diagnosisDate,
      diabetesType: _diabetesType,
    );
    await auth.updateProfile(updated);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Profile updated')),
    );
    Navigator.of(context).pop();
  }

  void _logout() {
    context.read<PhotosProvider>().clear();
    context.read<AuthProvider>().signOut();
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Profile')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(labelText: 'Full name'),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Required' : null,
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(labelText: 'Phone number'),
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
                ),
                const SizedBox(height: 28),
                ElevatedButton(
                  onPressed: _save,
                  child: const Text('Save Changes'),
                ),
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  onPressed: _logout,
                  icon: const Icon(Icons.logout, color: AppColors.healingBad),
                  label: const Text('Log Out',
                      style: TextStyle(color: AppColors.healingBad)),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(54),
                    side: const BorderSide(color: AppColors.healingBad),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
