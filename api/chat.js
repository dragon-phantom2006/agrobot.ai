import { GoogleGenerativeAI } from "@google/generative-ai";

const genai = new GoogleGenerativeAI(
  process.env.GEMINI_API_KEY   // ✅ must match Vercel env name
);

const model = genai.getGenerativeModel({
  model: "gemini-1.5-flash",
});

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { message } = req.body;

  if (!message) {
    return res.status(400).json({ error: "Message is required" });
  }

  try {
    const chatSession = model.startChat({
      history: [
        {
          role: "user",
          parts: [
            {
              text:
                   "You are AGROBOAT, an agriculture assistant.\n" +
                   "Follow user instructions STRICTLY.\n" +
                   "If user asks for points, respond ONLY in numbered points and base the points strictly on the immediately previous assistant message unless otherwise specified.\n" +
                   "If user asks for a paragraph, respond ONLY in paragraph form.\n" +
                   "If user specifies an exact number of points, give EXACTLY that number.\n" +
                   "Do not mix formats."

            }
          ]
        }
      ]
    });

    const result = await chatSession.sendMessage(message);
    res.status(200).json({ reply: result.response.text() });

  } catch (err) {
    console.error(err);
    res.status(500).json({ reply: "❌ Backend error" });
  }
}

