import argparse
import numpy as np
import matplotlib.pyplot as plt
import os


def get_signal_with_outliers(
    num_inliers=40,
    num_outliers=10,
    m=2.0,
    b=-1.5,
    noise_sigma=0.8,
    b_off=0.0,
    xrange=[0, 20],
):
    """Note that the 'num_outliers' may not be strictly accurate,
    since I have simply used another model to generate those points
    and added them to the original set."""
    N = num_inliers + num_outliers
    xs = min(xrange) + (max(xrange) - min(xrange)) * np.random.rand(N)
    noises = np.random.normal(scale=noise_sigma, size=N)
    outlier_noises = np.zeros(N)
    outlier_noises[:num_outliers] = b_off + np.random.normal(
        scale=6 * noise_sigma, size=num_outliers
    )
    np.random.shuffle(outlier_noises)
    ys = m * xs + b + noises + outlier_noises
    ys = m * xs + b + np.random.normal(scale=noise_sigma, size=N)
    ys[:num_outliers] += m * (2 * np.random.rand(num_outliers) - 1) * xs[
        :num_outliers
    ] + np.random.normal(scale=6 * noise_sigma, size=num_outliers)
    return xs, ys


def fit_line_least_squares(xs, ys):
    XS = np.zeros((len(ys), 2))
    XS[:, 0] = 1
    XS[:, 1] = xs
    betas = np.linalg.lstsq(XS, ys, rcond=None)[0]
    return betas[0], betas[1]


def fit_line_ransac(xs, ys, rounds=100, noise_sigma=0.8, s=2, chi_sq_thresh=3.84):
    best_num_inliers = 0
    best_m = None
    best_b = None

    def _get_num_inliers(b, m):
        residuals = (m * xs + b) - ys
        inlier_mask = (residuals**2) < chi_sq_thresh * (noise_sigma**2)
        return sum(inlier_mask.astype(int))

    for _ in range(rounds):
        ps = np.random.choice(np.arange(len(xs)), size=s)
        b, m = fit_line_least_squares(xs[ps], ys[ps])
        num_inliers = _get_num_inliers(b, m)
        if num_inliers > best_num_inliers:
            best_num_inliers = num_inliers
            best_b = b
            best_m = m

    return best_b, best_m


def compute_mean_squared_error(xs, ys, b, m):
    X = np.ones((len(ys), 2))
    X[:, 0] = 1
    X[:, 1] = xs
    errors = ys - X @ np.array([b, m])
    return np.mean(errors**2)


def plot_result(ax, xs, ys, xs_eval, ys_eval, b, m):
    ax.scatter(xs, ys)
    ax.scatter(xs_eval, ys_eval)
    ax.set_aspect("equal", "box")
    dx = max(xs) - min(xs)
    xl = np.array([min(xs) - 0.1 * dx, max(xs) + 0.1 * dx])
    ax.plot(xl, m * xl + b, "k")
    ax.set_xlim(xl)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int)
    parser.add_argument("--approach", choices=('lstsq', 'ransac'))
    parser.add_argument("--savedir", default="/results/")
    args = parser.parse_args()
    np.random.seed(args.seed)

    # Create the data
    m = 2 * np.random.rand() - 1
    b = 8 * np.random.rand() - 4
    xs_train, ys_train = get_signal_with_outliers(
        num_inliers=30, num_outliers=15, m=m, b=b)
    xs_eval, ys_eval = get_signal_with_outliers(
        num_inliers=20, num_outliers=0, m=m, b=b)

    # Evaluate
    if args.approach == "lstsq":
        b, m = fit_line_least_squares(xs_train, ys_train)
        mean_sq_error = compute_mean_squared_error(xs_eval, ys_eval, b, m)
    elif args.approach == "ransac":
        b, m = fit_line_ransac(xs_train, ys_train)
        mean_sq_error = compute_mean_squared_error(xs_eval, ys_eval, b, m)
    else:
        raise ValueError(f"Approach {args.approach} not recognized.")

    # Write the data to file
    rfname = f"results_{args.approach}_{args.seed}.csv"
    rfigname = f"results_{args.approach}_{args.seed}.png"
    with open(os.path.join(args.savedir, rfname), "w") as results_file:
        results_file.write(f"{mean_sq_error}")

    # Save the figure
    plt.figure(figsize=(8, 8))
    plot_result(plt.gca(), xs_train, ys_train, xs_eval, ys_eval, b, m)
    plt.savefig(os.path.join(args.savedir, rfigname), dpi=300)
