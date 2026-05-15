import React, { useState } from 'react';
import { track } from '../telemetry/pilot';
import styles from './FeedbackEmoji.module.css';

const EMOJIS = ['😊', '😐', '☹️'];

export default function FeedbackEmoji({ screenName }) {
  const [selected, setSelected] = useState(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');

  const handleSelect = (emoji, index) => {
    setSelected(index);
    track('feedback', { screen: screenName, emoji });
    if (index === 2) { // solo para ☹️
      setShowComment(true);
    } else {
      setShowComment(false);
    }
  };

  const handleCommentSubmit = () => {
    if (comment.trim()) {
      track('feedback_comment', { screen: screenName, comment: comment.trim().substring(0, 100) });
    }
    setShowComment(false);
    setComment('');
  };

  return (
    <div className={styles.container}>
      {selected === null ? (
        <div className={styles.emojiRow}>
          {EMOJIS.map((emoji, i) => (
            <button
              key={i}
              className={styles.emojiBtn}
              onClick={() => handleSelect(emoji, i)}
              aria-label={`Reacción ${i}`}
            >
              {emoji}
            </button>
          ))}
        </div>
      ) : showComment ? (
        <div className={styles.commentBox}>
          <input
            type="text"
            placeholder="Cuéntanos qué pasó"
            maxLength={100}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className={styles.commentInput}
          />
          <button className={styles.commentSend} onClick={handleCommentSubmit}>Enviar</button>
        </div>
      ) : (
        <div className={styles.thanks}>¡Gracias!</div>
      )}
    </div>
  );
}