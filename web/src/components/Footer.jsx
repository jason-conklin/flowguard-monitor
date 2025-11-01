export default function Footer() {
  return (
    <footer className="app-footer">
      <span>© {new Date().getFullYear()} FlowGuard</span>
      <span>Built with Flask, Celery, and React</span>
    </footer>
  );
}

