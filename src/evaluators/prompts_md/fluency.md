**System:**
You are an AI assistant. You will be given the definition of an evaluation metric for assessing the quality of an answer in a question-answering task. Your job is to compute an accurate evaluation score using the provided evaluation metric.

**User:**
Fluency measures the quality of individual sentences in the answer, and whether they are well-written and grammatically correct. Consider the quality of individual sentences when evaluating fluency. Given the question and answer, score the fluency of the answer between one to five stars using the following rating scale:
- One star: the answer completely lacks fluency
- Two stars: the answer mostly lacks fluency
- Three stars: the answer is partially fluent
- Four stars: the answer is mostly fluent
- Five stars: the answer has perfect fluency

This rating value should always be an integer between 1 and 5. So the rating produced should be 1 or 2 or 3 or 4 or 5.

**Question:** What did you have for breakfast today?
**Answer:** Breakfast today, me eating cereal and orange juice very good.
**Stars:** 1

**Question:** How do you feel when you travel alone?
**Answer:** Alone travel, nervous, but excited also. I feel adventure and like its time.
**Stars:** 2

**Question:** When was the last time you went on a family vacation?
**Answer:** Last family vacation, it took place in last summer. We traveled to a beach destination, very fun.
**Stars:** 3

**Question:** What is your favorite thing about your job?
**Answer:** My favorite aspect of my job is the chance to interact with diverse people. I am constantly learning from their experiences and stories.
**Stars:** 4

**Question:** Can you describe your morning routine?
**Answer:** Every morning, I wake up at 6 am, drink a glass of water, and do some light stretching. After that, I take a shower and get dressed for work. Then, I have a healthy breakfast, usually consisting of oatmeal and fruits, before leaving the house around 7:30 am.
**Stars:** 5

**Conversation History:**
{% for item in chat_history %}
    - **User:** {{ item.inputs }}
    - **Assistant:** {{ item.outputs }}
{% endfor %}

**Question:** {{question}}
**Answer:** {{answer}}
**Stars:**
