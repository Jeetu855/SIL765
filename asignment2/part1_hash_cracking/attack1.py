import hashlib
import time


def load_target_hashes(filename):
    with open(filename, "r") as f:
        return set(line.strip() for line in f if line.strip())


def crack_hashes(target_hashes, algo, wordlist_path):
    
    cracked = {}
    start_time = time.time()

    with open(wordlist_path, "rb") as wordlist_file:
        for line in wordlist_file:
            password = line.strip()
            hash_func = getattr(hashlib, algo)
            computed_hash = hash_func(password).hexdigest()

            if computed_hash in target_hashes:
                try:
                    cracked[computed_hash] = password.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    cracked[computed_hash] = password

    elapsed_time = time.time() - start_time
    return cracked, elapsed_time


def process_algorithm(hash_file, algo, wordlist_path):
    
    target_hashes = load_target_hashes(hash_file)
    cracked, elapsed_time = crack_hashes(target_hashes, algo, wordlist_path)

    print(f"{algo.upper()} Cracked Passwords:")
    for h, password in cracked.items():
        print(f"{h} -> {password}")

    print("\nUncracked Hashes:")
    for h in target_hashes:
        if h not in cracked:
            print(f"{h} -> No hash found in a line")

    print(f"\nTime taken for {algo.upper()} cracking: {elapsed_time:.2f} seconds\n")


def main():
    md5_file = "md5_hashes.txt"
    sha1_file = "sha1_hashes.txt"
    sha256_file = "sha256_hashes.txt"
    wordlist_path = "/usr/share/wordlists/rockyou.txt"

    process_algorithm(md5_file, "md5", wordlist_path)
    process_algorithm(sha1_file, "sha1", wordlist_path)
    process_algorithm(sha256_file, "sha256", wordlist_path)


if __name__ == "__main__":
    main()
