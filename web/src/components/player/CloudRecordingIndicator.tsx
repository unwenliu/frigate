import { IoCloud } from "react-icons/io5";
import { cn } from "@/lib/utils";
import ActivityIndicator from "@/components/indicators/activity-indicator";
import { useTranslation } from "react-i18next";

type CloudRecordingIndicatorProps = {
  hasCloudSource: boolean;
  isLoading?: boolean;
  className?: string;
};

export function CloudRecordingIndicator({
  hasCloudSource,
  isLoading = false,
  className,
}: CloudRecordingIndicatorProps) {
  const { t } = useTranslation(["components/player"]);

  if (!hasCloudSource) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 rounded-full bg-secondary/80 px-2 py-1 text-xs text-secondary-foreground backdrop-blur-sm",
        className
      )}
    >
      {isLoading ? (
        <>
          <ActivityIndicator className="size-3" size={12} />
          <span>{t("cloudRecording.loadingFromCloud", "Loading from cloud...")}</span>
        </>
      ) : (
        <>
          <IoCloud className="size-3 text-blue-400" />
          <span>{t("cloudRecording.source", "Cloud")}</span>
        </>
      )}
    </div>
  );
}
