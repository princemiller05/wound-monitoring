import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import 'home_screen.dart';
import 'photo_history_screen.dart';
import 'progress_screen.dart';
import 'edit_profile_screen.dart';

/// The shell that holds the four main tabs with a persistent bottom nav bar.
class MainScaffold extends StatefulWidget {
  const MainScaffold({super.key});

  @override
  State<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends State<MainScaffold> {
  int _index = 0;

  void _goToTab(int i) => setState(() => _index = i);

  @override
  Widget build(BuildContext context) {
    final pages = [
      HomeScreen(onNavigateToTab: _goToTab),
      const PhotoHistoryScreen(),
      const ProgressScreen(),
      const _ProfileTab(),
    ];

    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _goToTab,
        backgroundColor: Colors.white,
        indicatorColor: AppColors.primaryLight,
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'Home'),
          NavigationDestination(
              icon: Icon(Icons.photo_library_outlined),
              selectedIcon: Icon(Icons.photo_library),
              label: 'My Photos'),
          NavigationDestination(
              icon: Icon(Icons.show_chart_outlined),
              selectedIcon: Icon(Icons.show_chart),
              label: 'Progress'),
          NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person),
              label: 'Profile'),
        ],
      ),
    );
  }
}

/// Simple profile tab: shows key details and a button to edit.
class _ProfileTab extends StatelessWidget {
  const _ProfileTab();

  @override
  Widget build(BuildContext context) {
    final patient = context.watch<AuthProvider>().patient;
    if (patient == null) return const SizedBox.shrink();

    Widget row(String label, String? value) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 130,
                child: Text(label,
                    style: const TextStyle(color: AppColors.textMuted)),
              ),
              Expanded(
                child: Text(value == null || value.isEmpty ? '—' : value,
                    style: const TextStyle(
                        color: AppColors.textDark,
                        fontWeight: FontWeight.w500)),
              ),
            ],
          ),
        );

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.screenPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: CircleAvatar(
                  radius: 42,
                  backgroundColor: AppColors.primaryLight,
                  child: Text(
                    patient.fullName.isNotEmpty
                        ? patient.fullName[0].toUpperCase()
                        : '?',
                    style: const TextStyle(
                        fontSize: 36,
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(patient.fullName,
                    style: const TextStyle(
                        fontSize: 22, fontWeight: FontWeight.bold)),
              ),
              Center(
                child: Text(patient.email,
                    style: const TextStyle(color: AppColors.textMuted)),
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      row('Phone', patient.phone),
                      row('Height', patient.heightCm != null
                          ? '${patient.heightCm!.toStringAsFixed(0)} cm'
                          : null),
                      row('Weight', patient.weightKg != null
                          ? '${patient.weightKg!.toStringAsFixed(0)} kg'
                          : null),
                      row('BMI', patient.bmi?.toStringAsFixed(1)),
                      row('Doctors', patient.doctorEmails.isEmpty
                          ? 'None added'
                          : patient.doctorEmails.join(', ')),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                      builder: (_) => const EditProfileScreen()),
                ),
                icon: const Icon(Icons.edit),
                label: const Text('Edit Profile'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
