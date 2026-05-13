import { useTranslation } from "react-i18next";
import { BookOpen, FileText, HelpCircle, Lightbulb } from "lucide-react";

interface TeacherHomeProps {
  onSendMessage: (content: string) => void;
}

interface FeatureCard {
  id: string;
  icon: React.ReactNode;
  titleKey: string;
  descKey: string;
  prompt: string;
  color: string;
}

const FEATURES: FeatureCard[] = [
  {
    id: "lesson-plan",
    icon: <BookOpen className="h-6 w-6" />,
    titleKey: "teacher.feature.lessonPlan.title",
    descKey: "teacher.feature.lessonPlan.desc",
    prompt: "帮我生成一节教案，请告诉我学科、年级和课题",
    color: "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
  },
  {
    id: "quiz-gen",
    icon: <FileText className="h-6 w-6" />,
    titleKey: "teacher.feature.quizGen.title",
    descKey: "teacher.feature.quizGen.desc",
    prompt: "帮我生成试题，请告诉我学科、年级、知识点和题型要求",
    color: "bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400",
  },
  {
    id: "reflection",
    icon: <Lightbulb className="h-6 w-6" />,
    titleKey: "teacher.feature.reflection.title",
    descKey: "teacher.feature.reflection.desc",
    prompt: "帮我做教学反思，请描述你的课堂情况",
    color: "bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400",
  },
  {
    id: "qa",
    icon: <HelpCircle className="h-6 w-6" />,
    titleKey: "teacher.feature.qa.title",
    descKey: "teacher.feature.qa.desc",
    prompt: "你好，我有一个教学相关的问题想咨询",
    color: "bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-400",
  },
];

export function TeacherHome({ onSendMessage }: TeacherHomeProps) {
  const { t } = useTranslation();

  return (
    <div className="flex h-full flex-col items-center justify-center px-6 pb-24">
      <div className="w-full max-w-2xl space-y-8 animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold">{t("teacher.home.title")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("teacher.home.subtitle")}
          </p>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-2 gap-4">
          {FEATURES.map((feature) => (
            <button
              key={feature.id}
              type="button"
              onClick={() => onSendMessage(feature.prompt)}
              className="group flex flex-col items-start gap-3 rounded-xl border bg-card p-5 text-left transition-all hover:border-primary/40 hover:shadow-md"
            >
              <div className={`rounded-lg p-2.5 ${feature.color}`}>
                {feature.icon}
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">{t(feature.titleKey)}</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {t(feature.descKey)}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
