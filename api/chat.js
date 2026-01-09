import { GoogleGenerativeAI } from "@google/generative-ai";

export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    if (!process.env.GEMINI_API_KEY) {
      return res.status(500).json({
        error: "GEMINI_API_KEY missing"
      });
    }

    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    const genai = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

    const model = genai.getGenerativeModel({
      model: "gemini-1.5-flash"
    });

    const result = await model.generateContent(message);

    return res.status(200).json({
      reply: result.response.text()
    });

  } catch (err) {
    console.error("API crash:", err);
    return res.status(500).json({
      reply: "❌ Backend error",
      details: err.message
    });
  }
}

