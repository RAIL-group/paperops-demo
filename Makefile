## ==== Core Arguments and Parameters ====
MAJOR ?= 1
MINOR ?= 0
VERSION = $(MAJOR).$(MINOR)
IMAGE_NAME ?= paperops-demo

# Free parameters
NUM_SEEDS ?= 50

# Variables for Docker + building
.PHONY: build
DOCKER_BASE = docker run --init --ipc=host --rm \
	-it -w /paper \
	--volume="$(shell pwd)/paper/:/paper/:rw" \
	--volume="$(shell pwd)/src/:/src/:rw" \
	--volume="$(shell pwd)/results/:/results/:rw" \
	${IMAGE_NAME}:${VERSION}
build:
	@echo "Building the Docker container"
	@docker build -t ${IMAGE_NAME}:${VERSION} \
		-f ./Dockerfile .

# Specify what results we want and targets for evaluation
eval-lstsq-seeds = \
	$(shell for ii in $$(seq 10000 $$((10000 + $(NUM_SEEDS) - 1))); \
		do echo "results/results_lstsq_$${ii}.csv"; done)
eval-ransac-seeds = \
	$(shell for ii in $$(seq 10000 $$((10000 + $(NUM_SEEDS) - 1))); \
		do echo "results/results_ransac_$${ii}.csv"; done)
results/results_%.csv: seed = $(shell echo $@ | grep -Eo '[0-9]+' | tail -1)
results/results_%.csv: approach = $(shell echo $@ | grep -Eo '(lstsq|ransac)' | tail -1)
results/results_%.csv:
	@echo "Evaluating result for $(approach): $(seed)\n"
	@mkdir -p results/
	@$(DOCKER_BASE) python3 /src/evaluate_approach.py \
		--seed $(seed) --approach $(approach)

# Processed Results
processed-results-files = results/processed_scatterplot.png results/processed_results_data.pickle
results/processed_scatterplot.png: $(eval-lstsq-seeds) $(eval-ransac-seeds)
	@echo "Generating the results scatterplot."
	@$(DOCKER_BASE) python3 /src/process_results.py --output scatterplot
results/processed_results_data.pickle: $(eval-lstsq-seeds) $(eval-ransac-seeds)
	@echo "Generating the processed results pickle file."
	@$(DOCKER_BASE) python3 /src/process_results.py --output results_data

# Figures
rastered-figures = paper/figures/scatterplot.png
paper/figures/scatterplot.png: paper/figures/scatterplot.svg results/processed_scatterplot.png
	@$(DOCKER_BASE) inkscape --export-type=png --export-dpi=600 figures/scatterplot.svg

# Compile the paper
paper/main.pdf: paper/main.org $(processed-results-files) $(rastered-figures)
	@echo "Exporting and compiling the paper."
	@$(DOCKER_BASE) emacs main.org --eval "(progn \
		(setq org-babel-python-command \"python3\") \
		(setq org-confirm-babel-evaluate nil) \
		(setq confirm-kill-processes nil) \
		(org-babel-do-load-languages 'org-babel-load-languages '((python . t) (shell . t) (calc . t))) \
		(org-latex-export-to-pdf) \
		(save-buffers-kill-terminal))"

# Short commands for ease of use
evaluate: $(eval-lstsq-seeds) $(eval-ransac-seeds)
process-results: $(processed-results-files)
raster-figures: $(rastered-figures)
compile-paper: paper/main.pdf
clean:
	@echo "Removing built results."
	@rm -f $(processed-results-files) $(rastered-figures) paper/main.pdf paper/*.tex paper/*.tex~

clean-all: clean
	@echo "Cleaning all generated outputs (including results)."
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@$(MAKE) clean
	@rm -rf results/
	@echo "...done cleaning."
