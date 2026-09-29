import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import '../theme/app_theme.dart';

/// "My Doctors" — a patient can share their wound history with one or more
/// doctors by adding each doctor's email. Each doctor then sees this patient on
/// their dashboard (matched by email). Removing a doctor revokes their access.
class DoctorsScreen extends StatefulWidget {
  const DoctorsScreen({super.key});

  @override
  State<DoctorsScreen> createState() => _DoctorsScreenState();
}

class _DoctorsScreenState extends State<DoctorsScreen> {
  final _email = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    final e = _email.text.trim();
    if (e.isEmpty || !e.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid email')));
      return;
    }
    setState(() => _busy = true);
    await context.read<AuthProvider>().addDoctor(e);
    _email.clear();
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final doctors = context.watch<AuthProvider>().patient?.doctorEmails ?? [];

    // A single scrollable list holds everything (header + form + doctor cards)
    // so nothing needs an unbounded Expanded, and the page scrolls when the
    // keyboard is up.
    return Scaffold(
      appBar: AppBar(title: const Text('My Doctors')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          children: [
            Text(
              'Add your doctor\'s email to share your wound photos and healing '
              'with them. You can add more than one doctor, and remove any of '
              'them at any time.',
              style: AppText.muted,
            ),
            const SizedBox(height: 18),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              onSubmitted: (_) => _busy ? null : _add(),
              decoration: const InputDecoration(
                labelText: "Doctor's email",
                prefixIcon: Icon(Icons.medical_services_outlined),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: _busy ? null : _add,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Add doctor'),
            ),
            const SizedBox(height: 24),
            const Text('SHARED WITH', style: AppText.overline),
            const SizedBox(height: 8),
            if (doctors.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text('No doctors added yet', style: AppText.muted),
                ),
              )
            else
              ...doctors.map((email) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: AppColors.primaryLight,
                          child:
                              Icon(Icons.person, color: AppColors.primary),
                        ),
                        title: Text(email),
                        trailing: IconButton(
                          icon: const Icon(Icons.close,
                              color: AppColors.textMuted),
                          onPressed: () => context
                              .read<AuthProvider>()
                              .removeDoctor(email),
                        ),
                      ),
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}
