import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const audioFile = formData.get('audio') as File | null;
    const language = (formData.get('language') as string) || 'id';

    if (!audioFile) {
      return NextResponse.json(
        { error: 'Audio file is required' },
        { status: 400 }
      );
    }

    const ZAI = (await import('z-ai-web-dev-sdk')).default;
    const zai = await ZAI.create();

    // Convert audio file to base64
    const arrayBuffer = await audioFile.arrayBuffer();
    const buffer = Buffer.from(new Uint8Array(arrayBuffer));
    const base64Audio = buffer.toString('base64');

    const response = await zai.audio.asr.create({
      file_base64: base64Audio,
    });

    return NextResponse.json({
      success: true,
      transcription: response.text,
      detectedLanguage: language,
    });
  } catch (error) {
    console.error('ASR API Error:', error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'Gagal mengenali suara, silakan coba lagi',
      },
      { status: 500 }
    );
  }
}
