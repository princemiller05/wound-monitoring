// Edit the general health profile. Wound details live with each photo; doctors
// are managed from the home screen.
import 'package:flutter/material.dart';
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
  late TextEditingController _height;
  late TextEditingController _weight;

  @override
  void initState() {
    super.initState();
    final p = context.read<AuthProvider>().patient!;
    _name = TextEditingController(text: p.fullName);
    _phone = TextEditingController(text: p.phone ?? '');
    _height = TextEditingController(text: p.heightCm?.toString() ?? '');
    _weight = TextEditingController(text: p.weightKg?.toString() ?? '');
  }

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _height.dispose();
    _weight.dispose();
    super.dispose();
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
      heightCm: double.tryParse(_height.text.trim()),
      weightKg: double.tryParse(_weight.text.trim()),
      doctorEmails: old.doctorEmails,
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
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _height,
                        keyboardType: TextInputType.number,
                        decoration:
                            const InputDecoration(labelText: 'Height (cm)'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _weight,
                        keyboardType: TextInputType.number,
                        decoration:
                            const InputDecoration(labelText: 'Weight (kg)'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
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
