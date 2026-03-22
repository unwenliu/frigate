import { endOfHourOrCurrentTime } from "./dateUtil";
import { TimeRange } from "@/types/timeline";

/**
 *
 * @param timeRange
 * @returns timeRange chunked into individual hours
 */
export function getChunkedTimeDay(timeRange: TimeRange): TimeRange[] {
  const endOfThisHour = new Date(timeRange.before * 1000);
  endOfThisHour.setSeconds(0, 0);
  const data: TimeRange[] = [];
  const startDay = new Date(timeRange.after * 1000);
  startDay.setUTCMinutes(0, 0, 0);
  let start = startDay.getTime() / 1000;
  let end = 0;

  for (let i = 0; i < 24; i++) {
    startDay.setHours(startDay.getHours() + 1);

    if (startDay > endOfThisHour) {
      break;
    }

    end = endOfHourOrCurrentTime(startDay.getTime() / 1000);
    data.push({
      after: start,
      before: end,
    });
    start = startDay.getTime() / 1000;
  }

  data.push({
    after: start,
    before: Math.floor(timeRange.before),
  });

  return data;
}

export function getChunkedTimeRange(
  startTimestamp: number,
  endTimestamp: number,
) {
  const endOfThisHour = new Date();
  endOfThisHour.setHours(endOfThisHour.getHours() + 1, 0, 0, 0);
  const data: TimeRange[] = [];
  const startDay = new Date(startTimestamp * 1000);
  startDay.setUTCMinutes(0, 0, 0);
  let start = startDay.getTime() / 1000;
  let end = 0;

  while (end < endTimestamp) {
    startDay.setHours(startDay.getHours() + 1);

    if (startDay > endOfThisHour) {
      break;
    }

    end = endOfHourOrCurrentTime(startDay.getTime() / 1000);
    data.push({
      after: start,
      before: end,
    });
    start = startDay.getTime() / 1000;
  }

  return { start: startTimestamp, end: endTimestamp, ranges: data };
}

/**
 * 将时间范围分成15分钟的块
 * 这是为了避免超过 nginx-vod-module 的 MAX_CLIPS_PER_REQUEST = 16 限制
 * 每个块最多包含15个clips（15分钟，每分钟1个clip）
 *
 * @param timeRange
 * @returns timeRange chunked into 15-minute segments
 */
export function getChunkedTime15Min(timeRange: TimeRange): TimeRange[] {
  const endOfTime = new Date(timeRange.before * 1000);
  const data: TimeRange[] = [];
  const startTime = new Date(timeRange.after * 1000);

  // 将开始时间对齐到15分钟边界（0, 15, 30, 45分钟）
  startTime.setUTCSeconds(0, 0);
  const startMinute = startTime.getUTCMinutes();
  const alignedStartMinute = Math.floor(startMinute / 15) * 15;
  startTime.setUTCMinutes(alignedStartMinute, 0, 0);

  let start = startTime.getTime() / 1000;
  let end = 0;

  // 每15分钟一个块
  while (start < timeRange.before) {
    const nextTime = new Date(start * 1000);
    nextTime.setUTCMinutes(nextTime.getUTCMinutes() + 15);

    if (nextTime > endOfTime) {
      end = Math.floor(timeRange.before);
    } else {
      end = nextTime.getTime() / 1000;
    }

    data.push({
      after: start,
      before: end,
    });

    start = end;
  }

  return data;
}
