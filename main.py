# main.py - Run this file in PyCharm!
"""
RAG System with Role-Based Access Control
Interactive console version - No API server needed

How to use:
1. Add documents to documents/teacher/ and documents/student/
2. Right-click this file → Run 'main'
3. Follow the prompts in the Run window
"""

import os
from rag_engine import rag_engine


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 70)
    print(" RAG SYSTEM WITH ROLE-BASED ACCESS CONTROL (OLLAMA)")
    print("=" * 70)
    print("\n✓ Using Ollama - 100% Local - No API Needed!")
    print(f"✓ Model: {rag_engine.llm.model}")
    print("=" * 70)


def index_documents():
    """Index documents"""
    print("\n📚 INDEXING DOCUMENTS...")
    print("-" * 70)

    choice = input("\nDo you want to index documents now? (y/n): ").lower()

    if choice == 'y':
        rag_engine.index_documents()
        print("\n✅ Indexing complete!")
    else:
        print("\n⏭️  Loading existing indices...")
        rag_engine.load_existing_index()

        if rag_engine.teacher_vectorstore or rag_engine.student_vectorstore:
            print("✓ Loaded existing indices")
        else:
            print("⚠️  No indices found! Please index documents.")


def query_loop():
    """Main query loop"""
    print("\n" + "=" * 70)
    print(" QUERY INTERFACE")
    print("=" * 70)

    while True:
        print("\n" + "-" * 70)
        print("Select user role:")
        print("  1. Teacher (access all documents)")
        print("  2. Student (access only student documents)")
        print("  3. Re-index documents")
        print("  4. Exit")
        print("-" * 70)

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            role = 'teacher'
            print("\n🎓 Logged in as: TEACHER (Full Access)")
        elif choice == '2':
            role = 'student'
            print("\n👨‍🎓 Logged in as: STUDENT (Limited Access)")
        elif choice == '3':
            index_documents()
            continue
        elif choice == '4':
            print("\n👋 Goodbye!")
            print("=" * 70 + "\n")
            break
        else:
            print("\n❌ Invalid choice.")
            continue

        # Query sub-loop
        while True:
            print("\n" + "-" * 70)
            query = input("\n💭 Your question (or 'back' to change role, 'exit' to quit): ").strip()

            if query.lower() == 'exit':
                print("\n👋 Goodbye!")
                print("=" * 70 + "\n")
                return

            if query.lower() == 'back':
                break

            if not query:
                print("⚠️  Please enter a question.")
                continue

            try:
                print("\n🔍 Searching and generating answer...")
                result = rag_engine.query(query, role)

                print("\n" + "=" * 70)
                print(" ANSWER")
                print("=" * 70)
                print(f"\n{result['answer']}")

                if result['sources']:
                    print("\n" + "-" * 70)
                    print(" SOURCES")
                    print("-" * 70)
                    for i, source in enumerate(result['sources'], 1):
                        print(f"  {i}. {source['file']} ({source['access_level']})")

                print("\n" + "=" * 70)

            except Exception as e:
                print(f"\n❌ Error: {e}")


def check_setup():
    """Check folders and documents"""
    print("\n📋 CHECKING SETUP...")
    print("-" * 70)

    teacher_folder = "./documents/teacher"
    student_folder = "./documents/student"

    if not os.path.exists(teacher_folder):
        os.makedirs(teacher_folder)
        print(f"✓ Created: {teacher_folder}")

    if not os.path.exists(student_folder):
        os.makedirs(student_folder)
        print(f"✓ Created: {student_folder}")

    teacher_files = [f for f in os.listdir(teacher_folder)
                     if os.path.isfile(os.path.join(teacher_folder, f))]
    student_files = [f for f in os.listdir(student_folder)
                     if os.path.isfile(os.path.join(student_folder, f))]

    print(f"\n📄 Documents found:")
    print(f"   Teacher: {len(teacher_files)} files")
    print(f"   Student: {len(student_files)} files")

    if len(teacher_files) == 0 and len(student_files) == 0:
        print("\n⚠️  WARNING: No documents found!")
        print("   Add PDF, DOCX, TXT, or MD files to:")
        print(f"   - {teacher_folder}/")
        print(f"   - {student_folder}/")
        print()
        input("Press Enter to continue...")


def main():
    """Main function"""
    print_header()
    check_setup()
    index_documents()
    query_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
