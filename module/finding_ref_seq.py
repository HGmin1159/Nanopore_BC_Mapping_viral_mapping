import numpy as np
import faiss
import Levenshtein
from collections import Counter

base_dict = np.array([
    [1, 0, 0, 0],  # A
    [0, 1, 0, 0],  # T
    [0, 0, 1, 0],  # C
    [0, 0, 0, 1],  # G
    [0, 0, 0, 0]   # N (Padding)
])

char_to_index = {'A': 0, 'T': 1, 'C': 2, 'G': 3, 'N': 4}

def one_hot_encode(seq, ref_length):
    seq_length = len(seq)

    if seq_length < ref_length:
        seq += "N" * (ref_length - seq_length)
    elif seq_length > ref_length:
        seq = seq[:ref_length]

    seq_indices = np.array([char_to_index[char] for char in seq], dtype=np.int32)

    return base_dict[seq_indices].flatten()
 
def base_dist_encode(seq, base_to_index):
    return np.array([seq.count(base) for base in base_to_index])

class Finding_Reference_Seq:        
    def __init__(self, ref_base_to_index = ["A","T","C","G","AA","AT","AC","AG"], k=3, threshold=5):
        self.vector_dim = None
        self.vectors = None
        self.index = None
        self.reference_sequences = None
        self.ref_length = None
        self.k = k
        self.threshold = threshold
        self.ref_base_to_index = ref_base_to_index
        
            
    def load_reference_sequences(self, sequences):
        sequences = np.asarray(sequences).flatten()        
        
        sequences = [seq.upper() for seq in sequences if isinstance(seq, str)]
        sequences = list(set(sequences))
        self.reference_sequences = sequences
        
        length_counts = Counter(len(seq) for seq in sequences[:1000])
        self.ref_length = max(length_counts, key=length_counts.get)


        # processed_vectors = [one_hot_encode(seq, self.ref_length) for seq in sequences]
        self.seq_vectors = np.array([one_hot_encode(seq, self.ref_length) for seq in sequences], dtype="float32")
        self.vector_dim1 = 4 * self.ref_length 
        
        # processed_vectors = np.array([base_dist_encode(seq, self.ref_base_to_index) for seq in sequences], dtype="float32")
        self.base_vectors = np.array([base_dist_encode(seq, self.ref_base_to_index) for seq in sequences], dtype="float32")
        self.vector_dim2 = len(self.ref_base_to_index)

        self.index_seq = faiss.IndexFlatL2(self.vector_dim1)
        self.index_seq.add(self.seq_vectors)
        
        self.index_base = faiss.IndexFlatL2(self.vector_dim2)
        self.index_base.add(self.base_vectors)
        
    def find_similar_sequences(self, query_seq, k=None):
        if type(query_seq) != str:
            return None
        
        if k is None:
            k = self.k
            
        encoded_query = one_hot_encode(query_seq, self.ref_length)
        if encoded_query is None:
            return None 

        query_vec = np.array([encoded_query], dtype="float32")

        D_seq, I_seq = self.index_seq.search(query_vec, k)
        found_seqs_seq = {self.reference_sequences[i]: Levenshtein.distance(query_seq, self.reference_sequences[i]) for i in I_seq[0]}

        second_best_dist = sorted(found_seqs_seq.values())[1] if len(found_seqs_seq) > 1 else float("inf")
        
        found_seqs_base = {}
        if second_best_dist >= self.threshold:
            encoded_query_base = base_dist_encode(query_seq, self.ref_base_to_index)
            query_vec_base = np.array([encoded_query_base], dtype="float32")
            
            D_base, I_base = self.index_base.search(query_vec_base, k)
            found_seqs_base = {self.reference_sequences[i]: Levenshtein.distance(query_seq, self.reference_sequences[i]) for i in I_base[0]}

        combined_candidates = {**found_seqs_seq, **found_seqs_base}
        sorted_candidates = sorted(combined_candidates.items(), key=lambda x: x[1])

        return dict(sorted_candidates[:k])
    
    def find_most_probable_seq(self, query_seq):
        similar_seqs = self.find_similar_sequences(query_seq, self.k)

        if not similar_seqs:
            return None, None 
        
        filtered_seqs = {seq: dist for seq, dist in similar_seqs.items() if dist <= self.threshold}

        if not filtered_seqs:
            return None, None

        most_probable_seq = min(filtered_seqs, key=filtered_seqs.get)
        levenshtein_distance = filtered_seqs[most_probable_seq]

        return most_probable_seq, levenshtein_distance 
    
    def merging_reference_sequences(self, scores,threshold =2):
        if threshold is None :
            threshold = self.threshold
        sorted_sequences = sorted(self.reference_sequences, key=lambda seq: scores.get(seq, 0), reverse=True)
        merged_dict = {} 
        visited = set()

        for seq in sorted_sequences:
            if seq in visited:
                continue

            similar_seqs = self.find_similar_sequences(seq)
            if not similar_seqs:
                merged_dict[seq] = seq
                continue

            close_seqs = [s for s, dist in similar_seqs.items() if dist <= self.threshold and s not in visited]

            if close_seqs:
                best_seq = max(close_seqs, key=lambda s: scores.get(s, 0))
                merged_dict[best_seq] = best_seq 
                visited.update(close_seqs) 
            else:
                merged_dict[seq] = seq 


        self.reference_sequences = list(merged_dict.values())
        self.load_reference_sequences(self.reference_sequences)

        return None
        
