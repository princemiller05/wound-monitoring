import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'theme/app_theme.dart';
import 'providers/auth_provider.dart';
import 'providers/photos_provider.dart';
import 'screens/login_screen.dart';
import 'screens/main_scaffold.dart';

void main() {
  runApp(const WoundWatchApp());
}

class WoundWatchApp extends StatelessWidget {
  const WoundWatchApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => PhotosProvider()),
      ],
      child: MaterialApp(
        title: 'WoundWatch',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        // On launch: show Home if logged in, otherwise Login.
        home: Consumer<AuthProvider>(
          builder: (context, auth, _) =>
              auth.isLoggedIn ? const MainScaffold() : const LoginScreen(),
        ),
      ),
    );
  }
}
