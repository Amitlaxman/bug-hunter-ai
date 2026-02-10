from agents.orchestrator import run_pipeline_row
from dotenv import load_dotenv
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.getcwd())

load_dotenv()

# Sample 32 code (the one that was failing to find the bug)
code_32 = """RDI_BEGIN();
rdi.port("pt1").dc().pin("dig2").vForce(1 uA).burst();
rdi.port(TA::MULTI_PORT).func().burst("MPBurst2").burst(); // n
rdi.port("pt2").digCap().pin("dig1").samples(8).execute();
rdi.port(TA::MULTI_PORT).func().burst("MPBurst1").burst();
RDI_END();"""

print("--- TESTING SAMPLE 32 ---")
sample_id, bug_line, explanation = run_pipeline_row("32", code_32, verbose=True)
print("\nFINAL RESULT:")
print(f"ID: {sample_id}, Line: {bug_line}")
print(f"Explanation: {explanation}")
