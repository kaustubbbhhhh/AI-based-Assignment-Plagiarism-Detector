"""
Subject Validation Service.
Provides semantic matching to ensure the uploaded assignment matches the chosen subject.
Prevents students from uploading irrelevant files (e.g., Physics assignments to a CS class).
"""

import logging
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Dictionary of core concepts/keywords for each supported subject.
SUBJECT_KEYWORDS = {
    "Database Management Systems": [
        "sql", "database", "rdbms", "table", "query", "normalization", "bcnf", 
        "erd", "nosql", "mongodb", "transaction", "concurrency", "acid", 
        "relational", "schema", "foreign key", "primary key", "index"
    ],
    "Theory of Computation": [
        "automata", "turing", "dfa", "nfa", "regular expression", "context-free", 
        "pda", "computability", "decidability", "p vs np", "grammar", "chomsky", 
        "state", "transition", "language"
    ],
    "Probability, Statistics and Linear Programming": [
        "probability", "statistics", "distribution", "mean", "variance", 
        "standard deviation", "linear programming", "simplex", "objective function", 
        "constraints", "lpp", "hypothesis", "regression", "bayes", "poisson"
    ],
    "Circuits and Systems": [
        "circuit", "voltage", "current", "resistor", "capacitor", "inductor", 
        "kirchhoff", "thevenin", "norton", "op-amp", "amplifier", "frequency", 
        "bode plot", "laplace", "impedance", "node", "mesh"
    ],
    "Programming in Java": [
        "java", "class", "object", "inheritance", "polymorphism", "encapsulation", 
        "interface", "abstract", "jvm", "jre", "jdk", "exception", "thread", 
        "collection", "stream", "method", "variable", "compiler"
    ],
    "Compiler Design": [
        "compiler", "translator", "lexical analysis", "syntax", "grammar", "parser",
        "finite automata", "dfa", "nfa", "regular expression", "left recursion",
        "left factoring", "shift reduce", "operator precedence", "lr parsing",
        "slr", "lalr", "syntax directed translation", "sdd", "sdt", "intermediate code",
        "three-address code", "quadruples", "triples", "type checking", "symbol table",
        "error recovery", "code optimization", "loop optimization", "dag", "code generation",
        "peep-hole", "register allocation", "yacc", "lex"
    ],
    "Operating Systems": [
        "operating system", "process", "thread", "scheduling", "cpu scheduling",
        "mutual exclusion", "semaphore", "critical section", "deadlock", "banker's algorithm",
        "memory allocation", "paging", "segmentation", "virtual memory", "demand paging",
        "page replacement", "thrashing", "disk scheduling", "caching", "buffering",
        "file system", "file organization", "fat32", "ntfs", "ext2", "ext3", "ipc",
        "multiprogramming", "time sharing"
    ],
    "Computer Networks": [
        "network", "osi model", "tcp/ip", "physical layer", "data link layer",
        "transmission media", "error detection", "circuit switching", "packet switching",
        "flow control", "sliding window", "go-back-n", "selective repeat", "hdlc", "ppp",
        "multiple access", "ieee 802", "ethernet", "wifi", "token ring", "bridge",
        "routing", "congestion control", "ip addressing", "ipv4", "ipv6", "subnetting",
        "arp", "icmp", "udp", "tcp", "dns", "smtp", "ftp", "http", "socket"
    ],
    "Design and Analysis of Algorithm": [
        "algorithm", "asymptotic notation", "recurrence", "divide and conquer",
        "binary search", "merge sort", "quick sort", "greedy method", "knapsack",
        "huffman code", "spanning tree", "shortest path", "backtracking", "8 queens",
        "graph coloring", "hamiltonian", "dynamic programming", "matrix chain",
        "longest common subsequence", "floyd warshall", "branch and bound", "string matching",
        "rabin-karp", "kmp", "np-complete", "np-hard", "approximation algorithm", "ford-fulkerson"
    ],
    "Software Engineering": [
        "software engineering", "software crisis", "software process", "lifecycle model",
        "waterfall", "spiral model", "prototype", "srs", "requirements engineering",
        "dfd", "data dictionary", "er diagram", "project planning", "cocomo", "cost estimation",
        "risk management", "cohesion", "coupling", "software metrics", "halstead",
        "software reliability", "cmm", "iso 9001", "software testing", "boundary value",
        "equivalence class", "decision table", "path testing", "mutation testing",
        "unit testing", "integration testing", "debugging", "software maintenance"
    ],
    "Economics for Engineers": [
        "economics", "supply", "demand", "elasticity", "utility", "production cost",
        "market structure", "perfect competition", "monopoly", "oligopoly", "inflation",
        "interest rate", "present value", "depreciation", "capital budgeting", "cash flow",
        "cost-benefit analysis", "breakeven", "gdp", "monetary policy", "fiscal policy"
    ]
}

def validate_subject_relevance(text: str, subject: str) -> dict:
    """
    Validates if the extracted text is relevant to the selected subject.
    Returns {"is_valid": bool, "confidence": float, "reason": str}
    """
    if not text or len(text.strip()) < 50:
        return {"is_valid": True, "confidence": 1.0, "reason": "Text too short to confidently reject."}
        
    keywords = SUBJECT_KEYWORDS.get(subject)
    if not keywords:
        # If subject is not in our dictionary, we can't reliably reject it.
        return {"is_valid": True, "confidence": 1.0, "reason": "Subject not configured for validation."}
        
    text_lower = text.lower()
    
    # Count how many unique keywords are present
    matched_keywords = [kw for kw in keywords if kw in text_lower]
    
    # We require at least 2 unique keywords to be present for a standard assignment.
    # (This is a low threshold to prevent false positives)
    min_required = 2
    
    if len(matched_keywords) >= min_required:
        return {
            "is_valid": True, 
            "confidence": min(1.0, len(matched_keywords) / len(keywords)), 
            "reason": f"Found relevant keywords: {', '.join(matched_keywords[:3])}..."
        }

    confidence = len(matched_keywords) / max(1, len(keywords))
    if settings.SUBJECT_VALIDATION_STRICT:
        logger.warning(
            f"Subject mismatch rejected. Expected '{subject}', found keywords: {matched_keywords}"
        )
        return {
            "is_valid": False,
            "confidence": confidence,
            "reason": f"Subject mismatch detected for '{subject}'."
        }

    logger.warning(
        f"Subject mismatch allowed by policy (SUBJECT_VALIDATION_STRICT=false). Expected '{subject}', found keywords: {matched_keywords}"
    )
    return {
        "is_valid": True,
        "confidence": confidence,
        "reason": "Low subject match allowed by non-strict validation policy."
    }
