import argparse
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import scipy.stats
import os
import pickle
import re


def load_data(args):
    fnames = glob.glob(os.path.join(args.savedir, "*.csv"))
    all_seeds = set()
    data = {}
    for fname in fnames:
        seed = re.findall(r"\d+", fname)[-1]
        if "lstsq" in fname:
            approach = "lstsq"
        elif "ransac" in fname:
            approach = "ransac"
        else:
            raise ValueError(f"Approach {args.approach} not recognized.")
        dat = np.loadtxt(fname, dtype=float)
        all_seeds.add(seed)
        data[(seed, approach)] = dat

    all_seeds = list(all_seeds)
    lstsq_data = [data[(seed, "lstsq")] for seed in all_seeds]
    ransac_data = [data[(seed, "ransac")] for seed in all_seeds]
    return {
        "seeds": all_seeds,
        "lstsq_data": lstsq_data,
        "ransac_data": ransac_data,
    }


def make_scatterplot(args, data):
    lstsq_data = data["lstsq_data"]
    ransac_data = data["ransac_data"]
    lval = min(lstsq_data + ransac_data)
    hval = max(lstsq_data + ransac_data)
    dval = hval - lval
    spname = "processed_scatterplot.png"
    plt.figure(figsize=(8, 6))
    lims = [0, hval + 0.05 * dval]

    xy = np.vstack([lstsq_data, ransac_data])
    z = scipy.stats.gaussian_kde(xy)(xy)
    colors = plt.get_cmap("viridis")((z - z.min()) / (z.max() - z.min()))
    plt.gca().set_xlim(lims)
    plt.gca().set_ylim(lims)
    plt.gca().set_aspect("equal", "box")
    plt.plot(lims, lims, "k:", alpha=0.3)
    plt.scatter(lstsq_data, ransac_data, c=colors, s=10)
    plt.colorbar(ticks=[], label="Low Data Density            High Data Density")
    plt.savefig(os.path.join(args.savedir, spname), dpi=300)


def make_results_data(args, data):
    all_seeds = data["seeds"]
    lstsq_data = data["lstsq_data"]
    ransac_data = data["ransac_data"]

    with open(os.path.join(args.savedir, "processed_results_data.txt"), "w") as f:
        f.write(f"num_seeds {len(all_seeds)}\n")
        f.write(f"mse_lstsq {np.mean(lstsq_data)}\n")
        f.write(f"mse_ransac {np.mean(ransac_data)}\n")

    with open(
        os.path.join(args.savedir, "processed_results_data.pickle"), "wb"
    ) as handle:
        savedata = {
            "num_seeds": len(all_seeds),
            "mse_lstsq": np.mean(lstsq_data),
            "mse_ransac": np.mean(ransac_data),
        }
        pickle.dump(savedata, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--savedir", default="/results/")
    parser.add_argument("--output", choices=("scatterplot", "results_data"))
    args = parser.parse_args()
    data = load_data(args)
    if "scatterplot" in args.output:
        make_scatterplot(args, data)
    elif "results_data" in args.output:
        make_results_data(args, data)
