import 'package:flutter/material.dart';
import 'package:web/web.dart' as web;
import 'chat_screen.dart';
import 'llm_service.dart';
import 'login_screen.dart';

void main() {
  runApp(const ChatbotApp());
}

class ChatbotApp extends StatefulWidget {
  const ChatbotApp({super.key});

  @override
  State<ChatbotApp> createState() => _ChatbotAppState();
}

class _ChatbotAppState extends State<ChatbotApp> {
  String _token = '';

  @override
  void initState() {
    super.initState();
    _token = web.window.localStorage.getItem('access_key') ?? '';
  }

  Future<String?> _handleLogin(String token) async {
    try {
      await LlmService.validateAccessKey(token);
    } catch (_) {
      web.window.localStorage.removeItem('access_key');
      return 'Access key rejected. Please try again.';
    }

    web.window.localStorage.setItem('access_key', token);
    setState(() => _token = token);
    return null;
  }

  void _handleDisconnect() {
    web.window.localStorage.removeItem('access_key');
    setState(() => _token = '');
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Exam Tutor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1B5E20),
          brightness: Brightness.light,
        ),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        textSelectionTheme: const TextSelectionThemeData(
          selectionColor: Color(0xFF64B5F6),
          selectionHandleColor: Color(0xFF1565C0),
          cursorColor: Color(0xFF1B5E20),
        ),
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(24),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          filled: true,
          fillColor: Colors.grey[50],
        ),
      ),
      home: _token.isEmpty
          ? LoginScreen(onLogin: _handleLogin)
          : ChatScreen(
              accessKey: _token,
              onDisconnect: _handleDisconnect,
            ),
    );
  }
}
