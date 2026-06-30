import sys
import threading
import itertools
import time

from agent import run_agent
from document_generator import generate_document
from guardrails import validate_request, GuardrailError
from models import LLMError, DocumentError

DIVIDER = "\n" + "-" * 60 + "\n"


class Spinner:
    def __init__(self, message="Working"):
        self.message = message
        self.running = False
        self._thread = None

    def _spin(self):
        for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
            if not self.running:
                break
            sys.stdout.write(f"\r  {frame}  {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def start(self, message=None):
        if message:
            self.message = message
        self.running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, done_message=None):
        self.running = False
        if self._thread:
            self._thread.join()
        if done_message:
            print(f"  [OK]  {done_message}")


def print_tasks(tasks):
    print("\nPolicy Sections Generated:")
    for task in tasks:
        icon = "[DONE]" if task.status == "completed" else "[FAIL]"
        print(f"  {icon}  {task.task_name}")


def print_reflection(reflection):
    print("\nQuality Check:")
    status = "PASSED" if reflection.passed else "ISSUES FOUND"
    print(f"  Status: {status}")
    if reflection.issues_found:
        print("\n  Issues Found:")
        for issue in reflection.issues_found:
            print(f"    * {issue}")
    if reflection.improvements_made:
        print("\n  Improvements Applied:")
        for imp in reflection.improvements_made:
            print(f"    * {imp}")


def main():
    print(DIVIDER)
    print("  Insurance Policy Generation Agent")
    print("  Powered by Groq LLM + Autonomous Planning")
    print(DIVIDER)

    request = input("Enter your insurance policy request:\n> ").strip()
    request = request.encode("utf-8", errors="replace").decode("utf-8")

    if not request:
        print("No request entered. Exiting.")
        sys.exit(1)

    print(DIVIDER)

    spinner = Spinner()

    try:
        validate_request(request)

        spinner.start("Analysing request")
        policy_details = None
        tasks = None
        reflection = None

        result_holder = {}
        error_holder = {}

        def run():
            try:
                result_holder["result"] = run_agent(request, log=lambda _: None)
            except Exception as e:
                error_holder["error"] = e

        spinner.start("Generating policy")
        t = threading.Thread(target=run)
        t.start()

        dots = itertools.cycle(["   ", ".  ", ".. ", "..."])
        steps = [
            "Analysing request       ",
            "Planning policy sections",
            "Writing policy content  ",
            "Running quality check   ",
        ]
        step_duration = [3, 2, 40, 5]
        for step, duration in zip(steps, step_duration):
            spinner.running = False
            time.sleep(0.1)
            spinner.message = step
            spinner.running = True
            spinner._thread = threading.Thread(target=spinner._spin, daemon=True)
            spinner._thread.start()
            start = time.time()
            while time.time() - start < duration and t.is_alive():
                time.sleep(0.2)
            if not t.is_alive():
                break

        t.join()
        spinner.stop()

        if "error" in error_holder:
            raise error_holder["error"]

        result = result_holder["result"]

        spinner.start("Building document")
        doc_path = generate_document(
            request=request,
            policy_details=result["policy_details"],
            tasks=result["tasks"],
            reflection=result["reflection"],
        )
        spinner.stop("Document ready")

        print(DIVIDER)
        print_tasks(result["tasks"])
        print_reflection(result["reflection"])
        print(DIVIDER)
        print(f"Document saved to:\n  {doc_path}")
        print(DIVIDER)

    except GuardrailError as e:
        spinner.stop()
        print(f"\n[GUARDRAIL] Request blocked: {str(e)}")
        sys.exit(2)
    except LLMError as e:
        spinner.stop()
        print(f"\n[LLM ERROR] {str(e)}")
        sys.exit(1)
    except DocumentError as e:
        spinner.stop()
        print(f"\n[DOC ERROR] {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        spinner.stop()
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        spinner.stop()
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
