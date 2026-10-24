"""Exhaustive finite generator identity and source-label alias map; no targets."""
from collections import Counter
import engine as e


def main():
    key=e.keys()
    aliases=[]
    multiplicity=Counter()
    for (a,b), original in key.items():
        for sign in (-1,1):
            for offset in range(5):
                mapped=(sign*original[offset]%29,sign*original[offset+1]%29)
                canonical=key[mapped]
                assert canonical[:1176-offset]==[(sign*x)%29 for x in original[offset:]]
                assert canonical[:1105]==[(sign*original[offset+j])%29 for j in range(1105)]
                aliases.append({'a':a,'b':b,'sign':sign,'offset':offset,
                                'canonical_a':mapped[0],'canonical_b':mapped[1]})
                multiplicity[mapped]+=1
    assert len(aliases)==8410 and len(multiplicity)==841 and set(multiplicity.values())=={10}
    e.compact(e.HERE/'aliases.json',aliases)
    result={'schema':'fibonacci-finite-alias-proof-v1','generator_source_sha256':e.sha(e.LP/'analysis/campaign18_skip/armada/numeric_skip.py'),
            'beam_source_sha256':e.sha(e.LP/'analysis/campaign18_skip/sweep.py'),
            'formula':'G[j]=s*F[j+o] mod29; canonical(A,B)=(s*F[o],s*F[o+1]) mod29; sign+1,offset0; Atbash unchanged.',
            'algebra':'T=[[0,1],[1,1]], det(T)=-1 mod29; multiplication by sign is invertible. Each fixed(sign,offset) permutes all841seedpairs.',
            'generator_equalities_checked':8410,'minimum_complete_aligned_prefix_symbols':1172,
            'canonical_pairs':841,'preimages_per_pair':10,'canonical_needed_slots_max':1105,
            'largest_original_consumed_pointer':1108,'largest_source_padding_need':1120,'available_key_slots':1176,
            'boundary_proof':'Start o<=4; each of L-1 transitions advances1+d<=4; L<=277. Largest original pointer o+4*(L-1)<=1108. Source padding guard o+4*L+8<=1120<1176; no bounds or zero-padding divergence.',
            'tie_order_proof':'Map every pointer j to j-o. Plaintext, rejected-key equality, score/text/path and hypothesis enumeration order agree. Source sorts stably only by cumulative score, with no absolute-pointer or skip-count penalty. Ordered terminal beams agree after pointer translation; first maximum remains the same path.',
            'label_ordinal_formula':'(((((a*29+b)*2+sign_order)*2+atbash)*55+page_ordinal)*5+offset); sign_order0for-1,1for+1. Re-expand original aliases or minimize this ordinal to preserve tied best-label selection.',
            'source_labeled_screens':925100,'canonical_screens':92510,
            'aliases_sha256':e.sha(e.HERE/'aliases.json'),
            'scope_limit':'Exact declared recurrence, source widths and length<=277 only. Does not remove Atbash, change candidate rules or count841ideas.'}
    e.write(e.HERE/'proof-receipt.json',result)
    print('PASS:8410finite mappings,841canonical pairs,10preimages each; no target read')


if __name__=='__main__':
    main()
