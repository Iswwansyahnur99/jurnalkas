export default function handler(req, res) {
  if (req.method === "POST") {
    // handle login logic here
    res.status(200).json({ message: "Login sukses" });
  } else {
    res.status(405).json({ message: "Method not allowed" });
  }
}
