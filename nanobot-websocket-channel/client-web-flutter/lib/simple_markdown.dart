import 'package:flutter/material.dart';

/// Simple markdown renderer that handles **bold**, *italic*, and bullet lists.
/// Much lighter than flutter_markdown and works with Flutter 3.41.2 web.
class SimpleMarkdown extends StatelessWidget {
  final String data;
  final TextStyle? style;
  final bool selectable;

  const SimpleMarkdown({
    super.key,
    required this.data,
    this.style,
    this.selectable = false,
  });

  @override
  Widget build(BuildContext context) {
    final lines = data.split('\n');
    final widgets = <Widget>[];
    var inList = false;
    final listItems = <Widget>[];

    for (final line in lines) {
      if (line.startsWith('- ') || line.startsWith('• ')) {
        inList = true;
        final text = line.startsWith('- ') ? line.substring(2) : line.substring(2);
        listItems.add(_buildRichText(text, style));
      } else {
        if (inList && listItems.isNotEmpty) {
          widgets.add(Padding(
            padding: const EdgeInsets.only(left: 12, bottom: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: listItems
                  .map((item) => Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('• ', style: TextStyle(
                              fontSize: (style?.fontSize ?? 14.5),
                              color: style?.color ?? Colors.black87,
                            )),
                            Expanded(child: item),
                          ],
                        ),
                      ))
                  .toList(),
            ),
          ));
          listItems.clear();
        }
        inList = false;
        if (line.trim().isEmpty) {
          widgets.add(const SizedBox(height: 6));
        } else {
          widgets.add(_buildRichText(line, style));
        }
      }
    }

    if (inList && listItems.isNotEmpty) {
      widgets.add(Padding(
        padding: const EdgeInsets.only(left: 12, bottom: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: listItems
              .map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 2),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('• ', style: TextStyle(
                          fontSize: (style?.fontSize ?? 14.5),
                          color: style?.color ?? Colors.black87,
                        )),
                        Expanded(child: item),
                      ],
                    ),
                  ))
              .toList(),
        ),
      ));
    }

    return selectable
        ? SelectionArea(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: widgets))
        : Column(crossAxisAlignment: CrossAxisAlignment.start, children: widgets);
  }

  Widget _buildRichText(String text, TextStyle? baseStyle) {
    final theme = ThemeData.light();
    final defaultStyle = baseStyle ??
        const TextStyle(
          color: Color(0xFF212121),
          fontSize: 14.5,
          height: 1.5,
        );

    // Parse **bold** and *italic*
    final spans = <TextSpan>[];
    final pattern = RegExp(r'\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*');
    var lastEnd = 0;

    for (final match in pattern.allMatches(text)) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(text: text.substring(lastEnd, match.start), style: defaultStyle));
      }

      if (match.group(1) != null) {
        // ***bold italic***
        spans.add(TextSpan(
          text: match.group(1),
          style: defaultStyle.copyWith(
            fontWeight: FontWeight.bold,
            fontStyle: FontStyle.italic,
          ),
        ));
      } else if (match.group(2) != null) {
        // **bold**
        spans.add(TextSpan(
          text: match.group(2),
          style: defaultStyle.copyWith(fontWeight: FontWeight.bold),
        ));
      } else if (match.group(3) != null) {
        // *italic*
        spans.add(TextSpan(
          text: match.group(3),
          style: defaultStyle.copyWith(fontStyle: FontStyle.italic),
        ));
      }

      lastEnd = match.end;
    }

    if (lastEnd < text.length) {
      spans.add(TextSpan(text: text.substring(lastEnd), style: defaultStyle));
    }

    return spans.isEmpty
        ? Text(text, style: defaultStyle)
        : RichText(
            text: TextSpan(children: spans),
          );
  }
}
