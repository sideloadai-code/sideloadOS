"use client";

import { useEffect } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

interface RichTextEditorProps {
    initialContent: string;
    onChange: (html: string) => void;
}

/**
 * Extracted Tiptap editor component (Amendment 1).
 *
 * useEditor is called unconditionally at the top level of this component,
 * avoiding the Rules of Hooks crash that would occur if called conditionally
 * inside Workbench.tsx.
 */
export function RichTextEditor({ initialContent, onChange }: RichTextEditorProps) {
    // Amendment 2: Pass initialContent directly into useEditor config
    const editor = useEditor({
        extensions: [StarterKit],
        content: initialContent,
        immediatelyRender: false,
        editorProps: {
            attributes: {
                class: "outline-none min-h-[300px] px-4 py-3",
            },
        },
        onUpdate: ({ editor: e }) => {
            onChange(e.getHTML());
        },
    });

    // Amendment 2: Sync content if initialContent prop changes
    // (e.g., user clicks a different artifact without unmounting this component)
    useEffect(() => {
        if (editor && initialContent !== editor.getHTML()) {
            editor.commands.setContent(initialContent);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialContent]);

    if (!editor) {
        return null;
    }

    return (
        <div className="prose prose-invert max-w-none flex-1 overflow-auto">
            <EditorContent editor={editor} />
        </div>
    );
}
