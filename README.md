# 🧭 Lost & Found Web App 

A Flask-based web application to help users report and find lost or found items. It uses image recognition (ResNet + cosine similarity) to match found items with lost ones and notifies the rightful owner via email using Gmail SMTP.

---

## 🚀 Features

- 📝 Submit Lost or Found Items with description and image
- 🔍 Match found items with lost items using ResNet feature extraction + cosine similarity
- 📧 Email notification to owners on a potential match
- 🧠 AI-powered object feature comparison
- 📦 MySQL database integration

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **AI Model**: PyTorch ResNet18
- **Similarity Metric**: Cosine Similarity (via `sklearn`)
- **Mail Service**: Flask-Mail + Gmail SMTP
- **Frontend**: HTML, CSS, JavaScript
- **Image Processing**: `torchvision`, `PIL`

---

## 📸 Sample Flow

1. User reports a **lost item** (details + photo)
2. User reports a **found item** (details + photo)
3. App compares found image with all lost images using ResNet features
4. If similarity > 65%, a match is found and the owner is notified by email
5. Users can view their own lost item reports on a separate page
