import { truncateHead, truncateTail } from "@earendil-works/pi-coding-agent";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { StringDecoder } from "node:string_decoder";

export interface PreparedModelOutput {
  text: string;
  truncated: boolean;
  fullOutputPath?: string;
  totalBytes: number;
  totalLines: number;
}

/**
 * Bound text before it reaches the model and keep the complete text in a private file.
 * Keep the beginning ("head") for listings and file contents, or the end ("tail") for
 * logs and command output whose errors and final results come last.
 */
export async function prepareModelOutput(
  text: string,
  signal?: AbortSignal,
  keep: "head" | "tail" = "head",
): Promise<PreparedModelOutput> {
  signal?.throwIfAborted();
  const result = keep === "tail" ? truncateTail(text) : truncateHead(text);
  if (!result.truncated) {
    return {
      text,
      truncated: false,
      totalBytes: result.totalBytes,
      totalLines: result.totalLines,
    };
  }

  // truncateHead returns no content when the first line alone exceeds the byte limit.
  const body = result.firstLineExceedsLimit
    ? firstLinePrefix(text, result.maxBytes)
    : result.content;
  const directory = await mkdtemp(join(tmpdir(), "pi-tool-output-"));
  const fullOutputPath = join(directory, "output.txt");
  await writeFile(fullOutputPath, text, {
    encoding: "utf8",
    mode: 0o600,
    signal,
  });
  return {
    text: `${body}\n\n[Output truncated. Full output: ${fullOutputPath}]`,
    truncated: true,
    fullOutputPath,
    totalBytes: result.totalBytes,
    totalLines: result.totalLines,
  };
}

function firstLinePrefix(text: string, maxBytes: number): string {
  const lineEnd = text.indexOf("\n");
  const firstLine = lineEnd === -1 ? text : text.slice(0, lineEnd);
  // StringDecoder holds back an incomplete trailing character instead of emitting U+FFFD.
  return new StringDecoder("utf8").write(Buffer.from(firstLine, "utf8").subarray(0, maxBytes));
}
