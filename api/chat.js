import { GoogleGenerativeAI } from "@google/generative-ai";

const genai = new GoogleGenerativeAI(
  process.env.GEMINI_API_KEY
);

// Create model
const model = genai.getGenerativeModel({
  model: "gemini-2.5-flash",
});

// Start chat session with same system rules
let chatSession = model.startChat({
  history: [
    {
      role: "user",
      parts: [
        {
          text:
            "You are AGROBOAT, an agriculture assistant.\n" +
            "Follow user instructions STRICTLY.\n" +
            "If user asks for points, respond ONLY in numbered points.\n" +
            "If user asks for a paragraph, respond ONLY in paragraph form.\n" +
            "If user specifies an exact number of points, give EXACTLY that number.\n" +
            "Do not mix formats."
        }
      ]
    }
  ]
});

// API route
export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { message } = req.body;

  try {
    const result = await chatSession.sendMessage(message);
    const response = result.response.text();
    res.status(200).json({ reply: response });
  } catch (error) {
    res.status(500).json({
      reply: "❌ Error: " + error.message
    });
  }
}
