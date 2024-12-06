
import subprocess

# List of Python scripts to run
scripts = [

    "Code/Model_FJK/Scripts/random_forest_loop_agg.py",
    "Code/Model_FJK/Scripts/random_forest_loop_binned.py",
    "Code/Model_FJK/Scripts/random_forest_loop_count.py",
    "Code/Model_FJK/Scripts/random_forest_loop_climate.py",

    "Code/Model_FJK/Scripts/results_figures_agg.py",
    "Code/Model_FJK/Scripts/results_figures_binned.py",
    "Code/Model_FJK/Scripts/results_figures_count.py", 
    "Code/Model_FJK/Scripts/results_figures_climate.py",

]

print("Script Plan:")
for i, script in enumerate(scripts):
    print("     ", f"{i+1}: {script}")



# Run each script sequentially
for script in scripts:
    try:

        print("--" * 55)
        print("--" * 55)
        print("--" * 55)

        print(f"RUNNING {script}...")
        subprocess.run(["python", script], check=True)
        print(f"{script} COMPLETED.")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script}: {e}")
        break  # Stop execution if a script fails