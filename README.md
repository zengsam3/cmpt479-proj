# MBFL Fault Localization Tool

A **Mutation-Based Fault Localization (MBFL)** tool that implements MUSE-style fault localization using Defects4J mutation analysis data. This tool helps identify suspicious code locations that are likely to contain bugs by analyzing how mutants behave with failing and passing tests.

## Features

- **Multiple MBFL Methods**: Supports MUSE, Metallaxis, and DStar suspiciousness calculations
- **Defects4J Integration**: Parses standard Defects4J mutation analysis output files
- **Intelligent Test Matching**: Flexible test name matching to handle different test formats
- **Source Code Context**: Optional display of actual source code around suspicious lines
- **JSON Export**: Export results for further analysis or integration
- **Modular Design**: Clean, maintainable codebase with separated concerns

## Installation

1. Clone or download this repository
2. Install dependencies (optional, as the tool uses mostly built-in Python libraries):

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python3 main.py --mutation-dir /path/to/mutation/output --method muse --top-k 10
```

### With Source Code Context

```bash
python3 main.py --mutation-dir /path/to/mutation/output --source-dir /path/to/source/code --method muse --top-k 5
```

### Export Results to JSON

```bash
python3 main.py --mutation-dir /path/to/mutation/output --method metallaxis --output results.json
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mutation-dir` | Directory containing Defects4J mutation analysis output | **Required** |
| `--source-dir` | Source code directory for code context display | Optional |
| `--method` | MBFL method: `muse`, `metallaxis`, or `dstar` | `muse` |
| `--top-k` | Number of top suspicious locations to report | `10` |
| `--output` | Output JSON file for results | Optional |
| `--quiet` | Suppress detailed output | `false` |

## Required Input Files

The tool expects the following files in the `--mutation-dir`:

| File | Description | Required |
|------|-------------|----------|
| `mutants.log` | Mutant metadata and mutation operations | ✅ Yes |
| `kill.csv` | Mutant kill status (FAIL, LIVE, EXC, TIME, UNCOV) | ✅ Yes |
| `covMap.csv` | Test-mutant coverage mapping | ✅ Yes |
| `failing_tests` | List of failing test cases | ✅ Yes |
| `testMap.csv` | Test ID to test name mapping | ⚠️ Optional |

## MBFL Methods

### MUSE (Default)
```
Score = f2p / (f2f + p2f + 1)
```
- **Best for**: General fault localization
- **Characteristics**: Balanced approach, handles noise well

### Metallaxis
```
Score = f2p / (f2p + f2f)
```
- **Best for**: When you want to focus on failing test behavior
- **Characteristics**: More sensitive to failing tests

### DStar
```
Score = f2p² / (f2f + p2f)
```
- **Best for**: Emphasizing strong mutant-killing patterns
- **Characteristics**: Squares f2p to amplify strong signals

## Output Explanation

### Test Categories (f2p, f2f, p2p, p2f)

The debug output shows four categories of test-mutant interactions:

- **f2p**: **F**ailing test → **P**ass (mutant killed) - *Good sign for suspiciousness*
- **f2f**: **F**ailing test → **F**ail (mutant survives) - *Reduces suspiciousness*
- **p2p**: **P**assing test → **P**ass (mutant survives) - *Neutral*
- **p2f**: **P**assing test → **F**ail (mutant killed) - *Reduces suspiciousness*

### Sample Output

```
=== MBFL Analysis Results (MUSE) ===
Total suspicious locations: 226
Total mutants: 844
Failing tests: 2
Mutant status distribution: {'FAIL': 192, 'LIVE': 244, 'EXC': 193, 'TIME': 17, 'UNCOV': 198}

Top 5 Suspicious Locations:
--------------------------------------------------------------------------------
# 1: BigFraction:182 (score: 0.5000, mutants: 3)
>>> 182:     private BigFraction(double value, double epsilon, int maxIterations, int maxDenominator) {
    183:         long overflow = Integer.MAX_VALUE;
    184:         double r0 = value;
    185:         long a0 = (long)FastMath.floor(r0);
```

## Project Structure

```
mbfl-tool/
├── main.py                     # CLI entry point
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── src/
    ├── __init__.py
    ├── loader/                 # Data parsing modules
    │   ├── __init__.py
    │   ├── load_mutants.py     # Parses mutants.log
    │   ├── load_kill.py        # Parses kill.csv
    │   ├── load_coverage.py    # Parses covMap.csv + testMap.csv
    │   └── load_failures.py    # Parses failing_tests
    ├── core/                   # Core algorithms and models
    │   ├── __init__.py
    │   ├── model.py            # Data models
    │   ├── algorithm.py        # MBFL algorithms
    │   └── scorer.py           # Suspiciousness calculations
    └── report/                 # Output and reporting
        ├── __init__.py
        ├── ranker.py           # Ranking logic
        ├── printer.py          # Output formatting
        └── source_viewer.py    # Source code context
```

## Examples

### Example 1: Basic Fault Localization
```bash
python3 main.py --mutation-dir ./defects4j_output --method muse --top-k 5
```

### Example 2: With Source Code Context
```bash
python3 main.py --mutation-dir ./defects4j_output --source-dir ./project/src/main/java --method muse
```

### Example 3: Compare Different Methods
```bash
# Run MUSE
python3 main.py --mutation-dir ./defects4j_output --method muse --output muse_results.json

# Run Metallaxis  
python3 main.py --mutation-dir ./defects4j_output --method metallaxis --output metallaxis_results.json

# Run DStar
python3 main.py --mutation-dir ./defects4j_output --method dstar --output dstar_results.json
```

## Interpreting Results

### High Suspiciousness (> 0.4)
- Strong indication of faulty code
- Prioritize manual inspection of these locations

### Medium Suspiciousness (0.1 - 0.4)
- Moderate suspicion
- Check if multiple nearby lines have similar scores (might indicate a code block issue)

### Low Suspiciousness (< 0.1)
- Less likely to contain the fault
- May still be worth checking if it's in a critical code path

## Troubleshooting

### Common Issues

**"No mutant status data found"**
- Check that `kill.csv` exists and has the correct format
- Verify the CSV has proper headers and data rows

**"No failing tests found"**
- Ensure `failing_tests` file exists and contains test names
- MBFL requires at least one failing test to work effectively

**"Source file not found"**
- Check that `--source-dir` points to the correct Java source directory
- Ensure the directory structure matches the package names

**Test matching issues**
- The tool uses flexible test name matching
- Check the debug output for "Potential matches found" to verify test matching

### Debug Mode

For detailed debugging information, run without `--quiet` flag to see:
- Test matching details
- Sample f2p, f2f, p2p, p2f calculations
- Coverage statistics

## File Format Requirements

### mutants.log
```
1:LVR:POS:0:org.apache.commons.math3.fraction.BigFraction:45:1817:2 |==> 0
```

### kill.csv
```
MutantNo,Status
1,FAIL
2,LIVE
```

### covMap.csv
```
TestNo,MutantNo
197,751
198,752
```

### failing_tests
```
--- org.apache.commons.math3.fraction.BigFractionTest::testDigitLimitConstructor
--- org.apache.commons.math3.fraction.FractionTest::testDigitLimitConstructor
```

### testMap.csv (Optional)
```
TestNo,TestName
1,org.apache.commons.math3.exception.util.ArgUtilsTest
2,org.apache.commons.math3.genetics.FixedGenerationCountTest
```

## License

This tool is provided as-is for research and educational purposes. Please ensure compliance with any applicable licenses when using with Defects4J or other datasets.

## Contributing

To extend the tool:

1. **Add new MBFL methods**: Implement new scoring functions in `src/core/scorer.py`
2. **Add new parsers**: Create new parser modules in `src/loader/`
3. **Add new output formats**: Extend `src/report/printer.py`
4. **Enhance test matching**: Modify logic in `src/core/algorithm.py`
