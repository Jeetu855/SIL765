import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def load_salted_hashes(filename):
    
    salted_entries = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    salt, h = line.split(":")
                    salted_entries.append((salt, h))
                except ValueError:
                    continue
    return salted_entries


def load_wordlist(wordlist_path):
    with open(wordlist_path, "rb") as f:
        return [line.strip() for line in f if line.strip()]


def crack_single_entry(args):
    
    salt, target_hash, algo, wordlist = args
    hash_func = getattr(hashlib, algo)
    for password in wordlist:
        combined = password + salt.encode("utf-8")
        if hash_func(combined).hexdigest() == target_hash:
            try:
                return (salt, target_hash, password.decode("utf-8", errors="replace"))
            except UnicodeDecodeError:
                return (salt, target_hash, password)
    return None


def crack_salted_hashes_parallel(salted_entries, algo, wordlist, max_workers=None):
    
    start_time = time.time()
    cracked_results = []
    tasks = [(salt, h, algo, wordlist) for salt, h in salted_entries]

    if max_workers is None:
        max_workers = os.cpu_count() * 2  

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(crack_single_entry, task): task for task in tasks
        }
        for future in as_completed(future_to_task):
            result = future.result()
            if result is not None:
                cracked_results.append(result)

    elapsed_time = time.time() - start_time
    return cracked_results, elapsed_time


def process_algorithm(hash_file, algo, wordlist):
    salted_entries = load_salted_hashes(hash_file)
    cracked, elapsed_time = crack_salted_hashes_parallel(salted_entries, algo, wordlist)

    cracked_set = set((salt, h) for salt, h, _ in cracked)

    print(f"{algo.upper()} Salted Cracked Passwords:")
    for salt, h, password in cracked:
        print(f"Salt: {salt}, Hash: {h} -> Password: {password}")
    
    print("\nUncracked Hashes:")
    for salt, h in salted_entries:
        if (salt, h) not in cracked_set:
            print(f"Salt: {salt}, Hash: {h} -> No hash found in a line")

    print(
        f"\nTime taken for {algo.upper()} salted cracking: {elapsed_time:.2f} seconds\n"
    )


def main():
    # File paths
    md5_file = "md5_salted_hashes.txt"
    sha1_file = "sha1_salted_hashes.txt"
    sha256_file = "sha256_salted_hashes.txt"
    wordlist_path = "/usr/share/wordlists/rockyou.txt"

    print("Loading wordlist into memory...")
    wordlist = load_wordlist(wordlist_path)
    print(f"Wordlist loaded with {len(wordlist)} passwords.\n")

    process_algorithm(md5_file, "md5", wordlist)
    process_algorithm(sha1_file, "sha1", wordlist)
    process_algorithm(sha256_file, "sha256", wordlist)


if __name__ == "__main__":
    main()
