#!/usr/bin/env bash
# Fetches every public dataset used by the training scripts (GitHub raw only).
set -e
mkdir -p data/raw/smish && cd data/raw
g() { curl -sSL --fail -o "$2" "$1" && echo "ok $2"; }
g https://raw.githubusercontent.com/PHP4Life/Phishing-Email-Dataset/main/CEAS_08.csv CEAS_08.csv
g https://raw.githubusercontent.com/MWiechmann/enron_spam_data/master/enron_spam_data.zip enron_spam_data.zip && unzip -oq enron_spam_data.zip
g https://codeload.github.com/smurlafries1/MachineLearningPhishingDetection/zip/refs/heads/main fraud_repo.zip
unzip -oq fraud_repo.zip "MachineLearningPhishingDetection-main/fraud_email_.csv" && mv MachineLearningPhishingDetection-main/fraud_email_.csv fraud_email.csv && rmdir MachineLearningPhishingDetection-main
g https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv sms.tsv
g https://raw.githubusercontent.com/hcphap/Smishing-Dataset/main/LSDST-2022.csv.csv smish/hcphap_lsdst.csv
g https://raw.githubusercontent.com/shaghayegh-hp/Smishing_Dataset/main/Combined-Labeled-Dataset.csv smish/shaghayegh_combined.csv
g https://raw.githubusercontent.com/faizann24/Using-machine-learning-to-detect-malicious-URLs/master/data/data.csv url_strings.csv
g https://raw.githubusercontent.com/GregaVrbancic/Phishing-Dataset/master/dataset_full.csv url_features_full.csv
g https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-top-domains.txt opendns_top10k.txt
