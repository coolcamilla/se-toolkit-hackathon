import 'dart:async';
import 'package:flutter/material.dart';

import 'llm_service.dart';
import 'protocol.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final OutboundMessage? structured;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.structured,
  }) : timestamp = DateTime.now();

  factory ChatMessage.fromBotResponse(OutboundMessage response) {
    return ChatMessage(
      text: response.displayText,
      isUser: false,
      structured: response,
    );
  }
}

class ChatScreen extends StatefulWidget {
  final String accessKey;
  final VoidCallback? onDisconnect;

  const ChatScreen({
    super.key,
    required this.accessKey,
    this.onDisconnect,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late final LlmService _llm = LlmService();
  StreamSubscription<OutboundMessage>? _sub;
  StreamSubscription<bool>? _connSub;
  bool _isLoading = false;
  bool _isConnected = true;
  Timer? _slowResponseTimer;
  Timer? _hardResponseTimer;
  final Stopwatch _elapsed = Stopwatch();
  Timer? _elapsedTicker;

  static const _slowResponseDuration = Duration(seconds: 20);
  static const _hardResponseDuration = Duration(seconds: 120);

  @override
  void initState() {
    super.initState();
    _llm.connect(accessKey: widget.accessKey);
    _sub = _llm.responses.listen(
      (response) {
        _cancelResponseTimers();
        setState(() {
          _messages.add(ChatMessage.fromBotResponse(response));
          _isLoading = false;
        });
        _scrollToBottom();
      },
    );
    _connSub = _llm.connectionState.listen((connected) {
      if (!mounted) return;
      if (connected && !_isConnected) {
        _addBotMessage('Reconnected.');
      } else if (!connected && _isConnected) {
        _cancelResponseTimers();
        setState(() => _isLoading = false);
        _addBotMessage('Connection lost. Reconnecting...');
      }
      setState(() => _isConnected = connected);
    });
    _addBotMessage(
      'Welcome to your personal exam tutor! 🎓\n\n'
      'I can help you prepare for exams by asking questions, checking your answers, and giving feedback.\n\n'
      'Quick actions:\n'
      '• 📝 **Random Quiz** — test yourself with random questions\n'
      '• 🎯 **Training** — practice your weakest areas\n'
      '• ➕ **Add Question** — add your own questions\n'
      '• 🗑️ **Delete** — remove questions or entire topics\n'
      '• 🔍 **Search** — find questions by keyword\n\n'
      'Just tap a button or type a message to begin!',
    );
  }

  void _cancelResponseTimers() {
    _slowResponseTimer?.cancel();
    _hardResponseTimer?.cancel();
    _stopElapsed();
  }

  void _stopElapsed() {
    _elapsedTicker?.cancel();
    _elapsed.stop();
  }

  void _stopWaiting() {
    _llm.send('/stop');
    _cancelResponseTimers();
    setState(() => _isLoading = false);
  }

  void _startResponseTimeouts() {
    _slowResponseTimer?.cancel();
    _hardResponseTimer?.cancel();
    _slowResponseTimer = Timer(_slowResponseDuration, () {
      if (!mounted) return;
      _addBotMessage(
        'The assistant is still working on this request. '
        'Slow responses can happen when the model is busy.',
      );
    });
    _hardResponseTimer = Timer(_hardResponseDuration, () {
      if (!mounted) return;
      _addBotMessage(
        'This request is taking unusually long. '
        'Press the stop button to cancel and try again.',
      );
    });
  }

  void _addBotMessage(String text) {
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: false));
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading) return;

    _controller.clear();
    setState(() {
      _messages.add(ChatMessage(text: trimmed, isUser: true));
      _isLoading = true;
    });
    _scrollToBottom();

    _llm.send(trimmed);
    _elapsed.reset();
    _elapsed.start();
    _elapsedTicker = Timer.periodic(
      const Duration(seconds: 1),
      (_) => setState(() {}),
    );
    _startResponseTimeouts();
  }

  void _sendQuickAction(String text) {
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _isLoading = true;
    });
    _scrollToBottom();

    _llm.send(text);
    _elapsed.reset();
    _elapsed.start();
    _elapsedTicker = Timer.periodic(
      const Duration(seconds: 1),
      (_) => setState(() {}),
    );
    _startResponseTimeouts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.school_rounded,
                size: 20,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(width: 10),
            const Text('Exam Tutor'),
          ],
        ),
        backgroundColor: Theme.of(context).colorScheme.surface,
        foregroundColor: Theme.of(context).colorScheme.onSurface,
        actions: [
          if (widget.onDisconnect != null)
            IconButton(
              icon: const Icon(Icons.logout_rounded),
              tooltip: 'Disconnect',
              onPressed: widget.onDisconnect,
            ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(52),
          child: _buildQuickActions(),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: Container(
              color: Theme.of(context).colorScheme.surfaceContainerHighest
                  .withOpacity(0.3),
              child: SelectionArea(
                child: ListView.builder(
                  controller: _scrollController,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  itemCount: _messages.length + (_isLoading ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == _messages.length) {
                      return _buildLoadingBubble();
                    }
                    return _buildMessageBubble(_messages[index]);
                  },
                ),
              ),
            ),
          ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: Theme.of(context).colorScheme.surface,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _quickActionButton(Icons.quiz_outlined, 'Quiz', 'Start a random quiz'),
          _quickActionButton(
              Icons.fitness_center, 'Training', 'Practice weak areas'),
          _quickActionButton(Icons.add_circle_outline, 'Add', 'Add a question'),
          _quickActionButton(Icons.delete_outline, 'Delete', 'Remove questions'),
          _quickActionButton(Icons.search, 'Search', 'Find questions'),
        ],
      ),
    );
  }

  Widget _quickActionButton(IconData icon, String label, String tooltip) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: _isLoading
            ? null
            : () {
                switch (label) {
                  case 'Quiz':
                    _sendQuickAction('Start a random quiz');
                    break;
                  case 'Training':
                    _sendQuickAction('Start training mode');
                    break;
                  case 'Add':
                    _sendQuickAction('I want to add a question');
                    break;
                  case 'Delete':
                    _sendQuickAction('I want to delete a question or topic');
                    break;
                  case 'Search':
                    _sendQuickAction('search');
                    break;
                }
              },
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon,
                  size: 18,
                  color: Theme.of(context).colorScheme.onPrimaryContainer),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment:
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!message.isUser) _buildAvatar(false),
          const SizedBox(width: 6),
          Flexible(
            child: message.isUser
                ? _buildUserBubble(message)
                : _buildBotBubble(message),
          ),
          const SizedBox(width: 6),
          if (message.isUser) _buildAvatar(true),
        ],
      ),
    );
  }

  Widget _buildAvatar(bool isUser) {
    return CircleAvatar(
      radius: 14,
      backgroundColor: isUser
          ? Theme.of(context).colorScheme.primary
          : Theme.of(context).colorScheme.primaryContainer,
      child: Icon(
        isUser ? Icons.person_rounded : Icons.school_rounded,
        size: 16,
        color: isUser
            ? Colors.white
            : Theme.of(context).colorScheme.onPrimaryContainer,
      ),
    );
  }

  Widget _buildUserBubble(ChatMessage message) {
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.7,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(16),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(16),
          bottomRight: Radius.circular(4),
        ),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: SelectableText(
        message.text,
        style: const TextStyle(color: Colors.white, fontSize: 14.5),
      ),
    );
  }

  Widget _buildBotBubble(ChatMessage message) {
    final text = message.text;
    final score = _extractScore(text);

    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.8,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(16),
          bottomRight: Radius.circular(16),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 4,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (score != null) _buildScoreBadge(score),
          SelectableText(
            text,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface,
              fontSize: 14.5,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  /// Extract score like "78/100" from text.
  ({int score, int total})? _extractScore(String text) {
    final match = RegExp(r'(\d{1,3})/(\d{1,3})').firstMatch(text);
    if (match == null) return null;
    final score = int.tryParse(match.group(1)!);
    final total = int.tryParse(match.group(2)!);
    if (score == null || total == null) return null;
    return (score: score, total: total);
  }

  Widget _buildScoreBadge(({int score, int total}) data) {
    final pct = (data.score / data.total * 100).round();
    Color bgColor, textColor, iconColor;
    IconData icon;

    if (pct >= 80) {
      bgColor = Colors.green[100]!;
      textColor = Colors.green[800]!;
      iconColor = Colors.green[700]!;
      icon = Icons.check_circle;
    } else if (pct >= 50) {
      bgColor = Colors.amber[100]!;
      textColor = Colors.amber[900]!;
      iconColor = Colors.amber[800]!;
      icon = Icons.remove_circle;
    } else {
      bgColor = Colors.red[100]!;
      textColor = Colors.red[800]!;
      iconColor = Colors.red[700]!;
      icon = Icons.cancel;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 18, color: iconColor),
            const SizedBox(width: 6),
            Text(
              '$pct/${data.total}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 15,
                color: textColor,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStructuredMessage(OutboundMessage data) {
    if (data is ChoiceMessage) return _buildChoiceMessage(data);
    if (data is ConfirmMessage) return _buildConfirmMessage(data);
    if (data is CompositeMessage) return _buildCompositeMessage(data);
    return _buildBotBubble(ChatMessage(text: data.displayText, isUser: false));
  }

  Widget _buildChoiceMessage(ChoiceMessage data) {
    final content = data.content;
    final options = data.options;
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.8,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(16),
          bottomRight: Radius.circular(16),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 4,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (content.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: SelectableText(
                content,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                  fontSize: 14.5,
                  height: 1.5,
                ),
              ),
            ),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: options.map<Widget>((opt) {
              return ActionChip(
                label: Text(opt.label),
                onPressed: _isLoading ? null : () => _sendQuickAction(opt.value),
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                side: BorderSide.none,
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w500,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildConfirmMessage(ConfirmMessage data) {
    final content = data.content;
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.8,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(16),
          bottomLeft: Radius.circular(16),
          bottomRight: Radius.circular(16),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 4,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (content.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: SelectableText(
                content,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                  fontSize: 14.5,
                  height: 1.5,
                ),
              ),
            ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              FilledButton.icon(
                onPressed: _isLoading ? null : () => _sendQuickAction('yes'),
                icon: const Icon(Icons.check, size: 18),
                label: const Text('Yes'),
                style: FilledButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                onPressed: _isLoading ? null : () => _sendQuickAction('no'),
                icon: const Icon(Icons.close, size: 18),
                label: const Text('No'),
                style: OutlinedButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCompositeMessage(CompositeMessage data) {
    final parts = data.parts;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: parts.map<Widget>((part) {
        if (part is ChoiceMessage) return _buildChoiceMessage(part);
        if (part is ConfirmMessage) return _buildConfirmMessage(part);
        if (part is CompositeMessage) return _buildCompositeMessage(part);
        return _buildBotBubble(
            ChatMessage(text: part.displayText, isUser: false));
      }).toList(),
    );
  }

  Widget _buildLoadingBubble() {
    final seconds = _elapsed.elapsed.inSeconds;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            child: Icon(Icons.school_rounded,
                size: 16,
                color: Theme.of(context).colorScheme.onPrimaryContainer),
          ),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4),
                topRight: Radius.circular(16),
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 4,
                  offset: const Offset(0, 1),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  seconds > 0 ? 'Thinking… ${seconds}s' : 'Thinking…',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    final theme = Theme.of(context);
    final focusNode = FocusNode(
      onKeyEvent: (node, event) {
        if (event is KeyDownEvent &&
            event.logicalKey == LogicalKeyboardKey.enter &&
            !HardwareKeyboard.instance.isShiftPressed) {
          if (!_isLoading && _controller.text.trim().isNotEmpty) {
            _sendMessage(_controller.text);
            return KeyEventResult.handled;
          }
        }
        return KeyEventResult.ignored;
      },
    );
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          top: BorderSide(color: theme.colorScheme.outlineVariant),
        ),
      ),
      child: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                focusNode: focusNode,
                controller: _controller,
                decoration: InputDecoration(
                  hintText: 'Type your answer or a message...',
                  prefixIcon: const Padding(
                    padding: EdgeInsets.only(left: 16),
                    child: Icon(Icons.edit_note_outlined),
                  ),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
                textCapitalization: TextCapitalization.sentences,
                maxLines: 4,
                minLines: 1,
              ),
            ),
            const SizedBox(width: 8),
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: _isLoading
                  ? IconButton.filledTonal(
                      onPressed: _stopWaiting,
                      icon: const Icon(Icons.stop_rounded),
                      tooltip: 'Stop',
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.red[50],
                        foregroundColor: Colors.red[700],
                      ),
                    )
                  : IconButton.filled(
                      onPressed: () => _sendMessage(_controller.text),
                      icon: const Icon(Icons.send_rounded),
                      style: IconButton.styleFrom(
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _cancelResponseTimers();
    _sub?.cancel();
    _connSub?.cancel();
    _controller.dispose();
    _scrollController.dispose();
    _llm.dispose();
    super.dispose();
  }
}
