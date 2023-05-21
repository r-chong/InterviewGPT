# InterviewGPT

AI leetcode interviewer that assesses tech applicants. Built on Langchain and OpenAI APIs. Recruiter-focused and tracks progress and submits analysis to email.

![lnterviewGPT-1](https://github.com/r-chong/InterviewGPT/assets/75395781/74be3683-c9c6-404e-b9e1-a40c20d014df)

# Final features:

**Interview content**

-   AI interviewer: provides focused and structured interviews, asking one question at a time and ensuring comprehension by asking follow-up questions before moving to the next question
-   Two question types: code-based and concept questions
-   AI interacts beyond simply asking the question; it follows up and asks you to elaborate depending on your answer.
-   CLI with context: user-friendly experience with relevant information and instructions
    -   "Please enter a valid file path"
    -   "You can type in the chat for this question"
-   Records transcript with code: - enables detailed review of candidate's coding abilities and problem-solving techniques - gives insight into what the candidate codes like
-   Variable interview length: adjusts based on context, usually around 45 minutes.
-   I only have access to GPT 3.5 API so outputs will be greatly improved when I get the new API

**Backend**

-   Key validation on Firestore: enhances security, only registered candidates can access
-   Generate new keys
-   reference candidate emails

**Candidate Results**

-   MIM-formatted email that prettifies the outputs so recruiters can read them easier
-   Email notification: prompt feedback, improves candidate communication
-   For the email text, I used langchain to summarize the transcript and provide scores, stats, and give verdict on candidate
-   timestamps to measure speed; you can see how long the candidate took for each question, possible flagging if they answer too fast

**Prompting**

-   cut down Ack's original prompt to save tokens- AI interviewer: provides focused and structured interviews, asking one question at a time and ensuring comprehension by asking follow-up questions before moving to the next question

---

# How to set up CLI

You need Python and Git installed on your system.

1. Clone the repository:

- `git clone https://github.com/r-chong/InterviewGPT.git`
- `cd interviewgpt-cli`

2. Install the dependencies:
`pip install -r requirements.txt`

3. Setup your OpenAI api key and Google cloud api key

    Openai: 
    - Sign up for a developer account on OpenAI, they have $19 free credit you can use.
    - Go to API keys and generate new
    - Copy and paste into `openai_api-key` in `config.yaml`
    
    Google cloud api key: Turn on 2FA on your google account, go to account/security/2fa/app passwords. 
    - Generate a new key for Gmail on your chosen device
    - Copy and paste into `google_cloud_pass` in `config.yaml`

4. Setup FireStore database like this
![image](https://github.com/r-chong/InterviewGPT/assets/75395781/0e43f49f-1c71-419a-a71e-25e9a0fe34a6)
Download and reference serviceAccountKey.json

5. Run `python interviewgpt.py --context context.txt`
