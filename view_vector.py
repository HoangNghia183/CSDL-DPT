import argparse
import numpy as np
import os
import sys
import faiss

NPY_FEATS = "video_features_db.npy"
NPY_NAMES = "video_names_db.npy"
FAISS_INDEX = "vector_db.index"


def load_data():
	if not os.path.exists(NPY_FEATS):
		print(f"Không tìm thấy {NPY_FEATS}")
		sys.exit(1)
	feats = np.load(NPY_FEATS)
	names = None
	if os.path.exists(NPY_NAMES):
		names = np.load(NPY_NAMES, allow_pickle=True)
	return feats, names


def cmd_list(args):
	feats, names = load_data()
	print(f"count={feats.shape[0]}, dim={feats.shape[1]}")
	if names is not None:
		print(f"names loaded: {len(names)} entries")


def cmd_show(args):
	feats, names = load_data()
	idx = args.index
	if idx < 0 or idx >= feats.shape[0]:
		print("Index ngoài phạm vi")
		sys.exit(1)
	v = feats[idx]
	print(f"index={idx}")
	if names is not None:
		print(f"name={names[idx]}")
	print("vec[:10] =", v[:10].tolist())
	print("norm =", float(np.linalg.norm(v)))


def cmd_show_name(args):
	feats, names = load_data()
	if names is None:
		print("Không có file tên video")
		sys.exit(1)
	matches = np.where(names == args.name)[0]
	if len(matches) == 0:
		print("Không tìm thấy tên")
		sys.exit(1)
	idx = int(matches[0])
	v = feats[idx]
	print(f"index={idx}")
	print(f"name={names[idx]}")
	print("vec[:10] =", v[:10].tolist())
	print("norm =", float(np.linalg.norm(v)))


def cmd_stats(args):
	feats, names = load_data()
	norms = np.linalg.norm(feats, axis=1)
	print(f"count={feats.shape[0]}, dim={feats.shape[1]}")
	print(f"norms: min={norms.min():.4f}, mean={norms.mean():.4f}, max={norms.max():.4f}")


def cmd_dump(args):
	feats, names = load_data()
	out = args.out or 'vectors_sample.csv'
	n = min(args.n, feats.shape[0])
	import csv
	with open(out, 'w', newline='') as f:
		writer = csv.writer(f)
		for i in range(n):
			row = feats[i].tolist()
			if names is not None:
				row = [names[i]] + row
			writer.writerow(row)
	print(f"Wrote {n} vectors to {out}")


def cmd_faiss(args):
	if not os.path.exists(FAISS_INDEX):
		print(f"Không tìm thấy FAISS index {FAISS_INDEX}")
		sys.exit(1)
	idx = faiss.read_index(FAISS_INDEX)
	print('FAISS ntotal =', idx.ntotal)
	try:
		v = idx.reconstruct(0)
		print('reconstruct[0][:10] =', v[:10].tolist())
	except Exception as e:
		print('reconstruct không hỗ trợ cho index này:', e)


def main():
	p = argparse.ArgumentParser(description='Inspect video feature vectors')
	sp = p.add_subparsers(dest='cmd')

	sp_list = sp.add_parser('list')
	sp_list.set_defaults(func=cmd_list)

	sp_show = sp.add_parser('show')
	sp_show.add_argument('index', type=int)
	sp_show.set_defaults(func=cmd_show)

	sp_name = sp.add_parser('show-name')
	sp_name.add_argument('name')
	sp_name.set_defaults(func=cmd_show_name)

	sp_stats = sp.add_parser('stats')
	sp_stats.set_defaults(func=cmd_stats)

	sp_dump = sp.add_parser('dump')
	sp_dump.add_argument('--n', type=int, default=10)
	sp_dump.add_argument('--out', type=str, default=None)
	sp_dump.set_defaults(func=cmd_dump)

	sp_faiss = sp.add_parser('faiss')
	sp_faiss.set_defaults(func=cmd_faiss)

	args = p.parse_args()
	if not hasattr(args, 'func'):
		p.print_help()
		return
	args.func(args)


if __name__ == '__main__':
	main()